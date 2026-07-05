"""
Tam doküman özetleme motoru — map-reduce yaklaşımı.
Soru-cevap RAG yolundan bağımsız, doküman bazlı işler.
"""
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from openai import OpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)

_client = OpenAI(api_key=settings.OPENAI_API_KEY)

MAP_BATCH_SIZE = 5
MAX_WORKERS = 4
MAX_CHUNK_CHARS = 1200
LARGE_DOC_THRESHOLD = 150  # bu sayının üstünde süre uyarısı verilir

# Process-level in-memory cache: doc_id → summary result dict
_summary_cache: dict[str, dict] = {}

# ── Niyet tespiti ─────────────────────────────────────────────

_SUMMARY_VERBS = [
    "özetle", "özet ver", "özetini ver", "özetini çıkar",
    "özetler misin", "özetler mi",
    "ne anlatıyor", "ne hakkında", "ne var bu",
    "hangi konular", "hangi bölümler", "ana başlık",
    "içindekiler", "konuları neler", "konular neler",
    "bölümleri neler", "bölümler neler",
    "summarize", "summary",
]

_EXPLICIT_SUMMARY_VERBS = {
    "özetle", "özet ver", "özetini ver", "özetini çıkar",
    "özetler misin", "summarize", "summary",
}

_DOC_NOUNS = [
    "doküman", "belge", "dosya", "pdf", "kitap",
    "ders notu", "ders kitabı", "slayt",
    "son", "yüklediğim", "yüklenen",
]


def is_summarization_intent(message: str) -> bool:
    """Mesajın doküman düzeyinde özetleme/analiz isteği olup olmadığını belirle."""
    msg = message.lower()
    has_verb = any(v in msg for v in _SUMMARY_VERBS)
    has_noun = any(n in msg for n in _DOC_NOUNS)

    # Hem fiil hem doküman ismi → kesin özetleme
    if has_verb and has_noun:
        return True

    # "özetle" gibi kısa açık fiiller tek başına da yeterli
    if any(v in msg for v in _EXPLICIT_SUMMARY_VERBS):
        return True

    return False


# ── Doküman çözümleme ────────────────────────────────────────

def resolve_document(message: str) -> dict | None:
    """
    Mesajdan hangi dokümanın istendiğini belirle.
    - "son doküman" / "en son" → created_at DESC ilk kayıt
    - "X dokümanı" → dosya adında X geçiyor mu?
    - Eşleşme yoksa → en yeni doküman (fallback)
    """
    from app.db.repositories.documents_repo import get_documents

    docs = get_documents(source_module="knowledge_center")
    if not docs:
        # SGS Academy dokümanlarını da dene
        docs = get_documents()
    if not docs:
        return None

    msg_lower = message.lower()

    _LAST_KW = [
        "son doküman", "son belge", "son pdf", "son dosya",
        "en son", "en yeni", "son yüklediğim", "en son yüklediğim",
        "son yüklediğim",
    ]
    if any(kw in msg_lower for kw in _LAST_KW):
        # docs zaten created_at DESC sıralı
        logger.info(f"[summarizer] 'son doküman' → {docs[0].get('file_name')}")
        return docs[0]

    # Dosya adı eşleşmesi (4+ karakter kelimeler)
    words = re.findall(r"[A-Za-zÇçĞğİıÖöŞşÜü]{4,}", message)
    if words:
        for doc in docs:
            fname = (doc.get("file_name") or "").lower()
            matches = [w for w in words if w.lower() in fname]
            if len(matches) >= 2 or (len(matches) == 1 and len(matches[0]) >= 6):
                logger.info(f"[summarizer] ad eşleşmesi ({matches}) → {doc.get('file_name')}")
                return doc

    # Fallback: en yeni doküman
    logger.info(f"[summarizer] eşleşme yok, fallback → {docs[0].get('file_name')}")
    return docs[0]


# ── Map-Reduce özetleme ───────────────────────────────────────

def _map_batch(batch: list[dict], batch_idx: int, doc_name: str, total_chunks: int) -> str:
    """Bir chunk grubunu özetle — map aşaması."""
    parts = []
    for j, chunk in enumerate(batch):
        text = (chunk.get("chunk_data") or chunk.get("content") or "")[:MAX_CHUNK_CHARS]
        abs_idx = batch_idx * MAP_BATCH_SIZE + j + 1
        parts.append(f"[Parça {abs_idx}/{total_chunks}]\n{text}")

    batch_text = "\n\n".join(parts)
    prompt = (
        f'Aşağıdaki metin "{doc_name}" adlı dokümanın bir bölümüdür '
        f"({batch_idx * MAP_BATCH_SIZE + 1}-{batch_idx * MAP_BATCH_SIZE + len(batch)}. parçalar).\n"
        "Bu bölümün ana konularını ve önemli noktalarını 3-5 cümleyle özetle. "
        "Yalnızca verilen metinden üret; dışarıdan bilgi ekleme.\n\n"
        f"{batch_text}\n\nÖZET:"
    )
    try:
        resp = _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=350,
            temperature=0.2,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"[summarizer] map batch {batch_idx} hatası: {e}")
        return f"[Bölüm {batch_idx + 1} özetlenemedi]"


def _reduce(batch_summaries: list[str], doc_name: str, total_chunks: int) -> str:
    """Bölüm özetlerini birleştirip yapılandırılmış nihai özet üret — reduce aşaması."""
    sections = "\n\n".join(
        f"Bölüm {i + 1}: {s}" for i, s in enumerate(batch_summaries)
    )
    prompt = (
        f'"{doc_name}" dokümanının {total_chunks} parçasının bölüm özetleri aşağıdadır.\n\n'
        f"{sections}\n\n"
        "Bu özetleri kullanarak dokümanın KAPSAMLI yapılandırılmış özetini oluştur:\n\n"
        "## Ana Başlıklar\n"
        "Dokümanın tüm ana konularını liste halinde yaz.\n\n"
        "## Bölüm Özetleri\n"
        "Her ana konu için 2-4 cümlelik özet.\n\n"
        "## Kritik Notlar\n"
        "Sınav veya uygulama açısından özellikle önemli noktalar.\n\n"
        "KURAL: Her ana başlığa mutlaka değin. Yalnızca bir bölüme odaklanma. "
        "Başlıklar için ## kullan, maddeler için - kullan."
    )
    try:
        resp = _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.2,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"[summarizer] reduce hatası: {e}")
        return "\n\n---\n\n".join(batch_summaries)


def summarize_document(doc_id: str) -> dict:
    """
    Bir dokümanı map-reduce ile tam olarak özetle.

    Returns dict:
        doc_name: str
        total_chunks: int
        summary: str
        from_cache: bool
        large_doc: bool  — kullanıcıya süre uyarısı gerekli mi?
        error: str | None
    """
    if doc_id in _summary_cache:
        logger.info(f"[summarizer] cache hit: {doc_id[:8]}")
        return {**_summary_cache[doc_id], "from_cache": True}

    from app.db.repositories.documents_repo import get_document
    from app.db.repositories.chunks_repo import get_chunks_by_document_id

    doc = get_document(doc_id)
    if not doc:
        return {
            "doc_name": "", "total_chunks": 0, "summary": "",
            "from_cache": False, "large_doc": False,
            "error": f"Doküman bulunamadı: {doc_id}",
        }

    doc_name = doc.get("file_name", "Bilinmeyen doküman")

    if doc.get("status") not in ("indexed", None):
        pass  # indekslenmemiş olsa da chunk'ları dene

    chunks = get_chunks_by_document_id(doc_id)
    total_chunks = len(chunks)

    if total_chunks == 0:
        return {
            "doc_name": doc_name, "total_chunks": 0,
            "summary": "Bu doküman henüz indekslenmemiş veya içerik çıkarılamadı.",
            "from_cache": False, "large_doc": False, "error": None,
        }

    large_doc = total_chunks > LARGE_DOC_THRESHOLD
    logger.info(f"[summarizer] başlıyor: '{doc_name}' ({total_chunks} chunk, large={large_doc})")

    batches = [chunks[i:i + MAP_BATCH_SIZE] for i in range(0, total_chunks, MAP_BATCH_SIZE)]
    n_batches = len(batches)
    logger.info(f"[summarizer] map: {n_batches} batch × {MAP_BATCH_SIZE} chunk, {MAX_WORKERS} worker")

    # Map (paralel)
    batch_summaries: list[str | None] = [None] * n_batches
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_idx = {
            executor.submit(_map_batch, batch, i, doc_name, total_chunks): i
            for i, batch in enumerate(batches)
        }
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                batch_summaries[idx] = future.result()
            except Exception as e:
                logger.error(f"[summarizer] batch {idx} exception: {e}")
                batch_summaries[idx] = f"[Bölüm {idx + 1} işlenemedi]"

    logger.info("[summarizer] reduce başlıyor")
    summary = _reduce([s for s in batch_summaries if s], doc_name, total_chunks)

    result = {
        "doc_name": doc_name,
        "total_chunks": total_chunks,
        "summary": summary,
        "from_cache": False,
        "large_doc": large_doc,
        "error": None,
    }
    _summary_cache[doc_id] = result
    logger.info(f"[summarizer] tamamlandı: '{doc_name}' → cache'lendi")
    return result


def invalidate_summary_cache(doc_id: str) -> None:
    """Doküman yeniden işlendiğinde cache'i temizle."""
    _summary_cache.pop(doc_id, None)
    logger.info(f"[summarizer] cache temizlendi: {doc_id[:8]}")
