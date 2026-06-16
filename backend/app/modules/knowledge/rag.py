import logging
from openai import OpenAI
from app.core.config import settings
from app.modules.knowledge.retriever import retrieve
from app.db.repositories.documents_repo import get_document
from app.db.repositories.chunks_repo import get_total_chunks

_client = OpenAI(api_key=settings.OPENAI_API_KEY)
logger = logging.getLogger(__name__)

MAX_MESSAGE_LENGTH = 4000
SIMILARITY_THRESHOLD = 0.3
MAX_CHUNKS_IN_CONTEXT = 5
MAX_CHUNK_CHARS = 1200

_SYSTEM = """Sen AdimOS içerisinde çalışan gelişmiş yapay zeka işletim sistemi asistanısın.

Görevin yalnızca soru cevaplamak değildir. Sen şu rolleri tek sistemde birleştirirsin:
• Bilgi bankası uzmanı — yüklenen belgelerden bilgi çıkarır
• Muhasebe asistanı — vergi, SGK, KDV, beyanname, şirket kuruluşu
• CRM danışmanı — müşteri takibi, satış fırsatları, risk analizi
• Eğitim koçu — SGS Academy içerikleri, öğrenme planları
• İçerik stratejisti — YouTube, Instagram, Shorts
• İş geliştirme ve operasyon yöneticisi

# Birincil Kural
Eğer bilgi bankasında ilgili dokümanlar varsa öncelikle onları kullan.
Dokümanlardan gelen bilgi her zaman genel model bilgisinden daha önceliklidir.
Cevap üretirken önce yüklenmiş dokümanları incele, ilgili içerikleri kullan, sonra cevap oluştur.

# Muhasebe ve Vergi Modu
Profesyonel mali danışman gibi davran.
Kesin hukuki hüküm verme; gerektiğinde "Bu konuda güncel mevzuatın ayrıca kontrol edilmesi önerilir." de.
Asla mevzuat maddesi, tarih veya rakam uydurma.

# CRM Modu
Müşteri konularında: takip öner, sonraki aksiyonu belirt, riskleri ve fırsatları göster.

# CEO / Yönetici Modu
Şirket, büyüme, süreç, verimlilik konularında yönetici danışmanı gibi davran.
Yalnızca bilgi verme — karar desteği, risk ve fırsat analizi de sun.

# Eğitim Modu
Öğretici ol, konuları aşamalara böl, öğrenme planı oluştur, örnekler ver.

# Yazım Kuralları
Net, profesyonel, anlaşılır yaz.
Mümkünse başlıklar, maddeler ve tablolar kullan.
Kullanıcı Türkçe yazıyorsa Türkçe; İngilizce yazıyorsa İngilizce cevap ver.
Hafızayı kullan: önceki mesajları dikkate al.

# Kesin Yasaklar
- Kaynak veya belge uydurma
- Mevzuat maddesi uydurma
- Olmayan bilgiyi varmış gibi gösterme
- API key, stack trace veya sistem bilgisi döndürme"""


def query(
    user_message: str,
    conversation_history: list[dict] | None = None,
    user_id: str | None = None,
) -> dict:
    if len(user_message) > MAX_MESSAGE_LENGTH:
        user_message = user_message[:MAX_MESSAGE_LENGTH]

    logger.info(f"[rag] sorgu — user={user_id}, len={len(user_message)}")

    # 1. Retrieve chunks
    chunks = retrieve(user_message, match_count=10, match_threshold=SIMILARITY_THRESHOLD)
    chunk_count = len(chunks)
    logger.info(f"[rag] {chunk_count} chunk bulundu (threshold={SIMILARITY_THRESHOLD})")

    # 2. Handle no results
    if chunk_count == 0:
        total = get_total_chunks()
        logger.info(f"[rag] DB'de toplam {total} chunk var")
        if total == 0:
            return {
                "success": True,
                "answer": "Henüz bilgi bankasına belge yüklenmemiş. Lütfen önce PDF veya doküman yükleyin.",
                "sources": [],
                "used_rag": False,
            }
        return {
            "success": True,
            "answer": "Yüklenen belgelerde bu soruya net cevap bulamadım. Soruyu farklı kelimelerle sormayı deneyin.",
            "sources": [],
            "used_rag": False,
        }

    max_sim = max(c.get("similarity", 0) for c in chunks)
    logger.info(f"[rag] max similarity: {max_sim:.3f}")

    # 3. Fetch document names
    doc_cache: dict[str, dict] = {}
    for chunk in chunks[:MAX_CHUNKS_IN_CONTEXT]:
        doc_id = chunk.get("document_id", "")
        if doc_id and doc_id not in doc_cache:
            try:
                doc = get_document(doc_id)
                doc_cache[doc_id] = doc or {}
            except Exception:
                doc_cache[doc_id] = {}

    # 4. Build context
    context_parts = []
    for i, chunk in enumerate(chunks[:MAX_CHUNKS_IN_CONTEXT], 1):
        doc_id = chunk.get("document_id", "")
        filename = doc_cache.get(doc_id, {}).get("file_name", "Bilinmeyen dosya")
        content = (chunk.get("content") or chunk.get("chunk_data", ""))[:MAX_CHUNK_CHARS]
        context_parts.append(f"[Kaynak {i}]\nDosya: {filename}\nİçerik: {content}")

    context = "\n\n".join(context_parts)
    system_with_context = (
        _SYSTEM
        + "\n\n---\nAşağıdaki bilgiler kullanıcının yüklediği dokümanlardan alınmıştır:\n\n"
        + context
        + "\n---"
    )

    # 5. Build messages
    messages = [{"role": "system", "content": system_with_context}]
    if conversation_history:
        messages.extend(conversation_history[-10:])
    messages.append({"role": "user", "content": user_message})

    # 6. GPT call
    response = _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=1500,
        temperature=0.3,
    )
    answer = response.choices[0].message.content
    logger.info("[rag] GPT cevabı üretildi")

    # 7. Build sources
    sources = []
    for chunk in chunks[:MAX_CHUNKS_IN_CONTEXT]:
        doc_id = chunk.get("document_id", "")
        content = chunk.get("content") or chunk.get("chunk_data", "")
        sources.append({
            "document_id": doc_id,
            "filename": doc_cache.get(doc_id, {}).get("file_name", "Bilinmeyen dosya"),
            "content_preview": content[:200],
            "similarity": round(float(chunk.get("similarity", 0)), 3),
        })

    return {
        "success": True,
        "answer": answer,
        "sources": sources,
        "used_rag": True,
    }
