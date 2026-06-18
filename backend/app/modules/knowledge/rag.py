import re
import logging
from datetime import datetime, timedelta
from openai import OpenAI
from app.core.config import settings
from app.modules.knowledge.retriever import retrieve
from app.db.repositories.documents_repo import get_document
from app.db.repositories.chunks_repo import get_total_chunks

_client = OpenAI(api_key=settings.OPENAI_API_KEY)
logger = logging.getLogger(__name__)

MAX_MESSAGE_LENGTH = 4000
SIMILARITY_THRESHOLD = 0.3
GOOD_SIMILARITY = 0.5   # bu eşiğin altında kalırsa 2. arama yapılır
MAX_CHUNKS_IN_CONTEXT = 6
MAX_CHUNK_CHARS = 1200

def _safe_count(fn):
    try:
        return fn()
    except Exception:
        return 0


def _get_live_context() -> str:
    """
    Tüm agentlardan anlık veri topla ve chat'e context olarak enjekte et.
    Chat bu sayede 'bu hafta neler oldu', 'kaç lead var' sorularını cevaplar.
    """
    try:
        from app.db.supabase import get_supabase_client
        sb = get_supabase_client()
        today = datetime.utcnow().date()
        week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()

        def count(table, filters=None, since=None):
            q = sb.table(table).select("id", count="exact")
            if filters:
                for k, v in filters.items():
                    q = q.eq(k, v)
            if since:
                q = q.gte("created_at", since)
            try:
                return q.execute().count or 0
            except Exception:
                return 0

        # CRM
        total_leads    = count("leads")
        new_leads      = count("leads", {"status": "new"})
        followup_leads = count("leads", {"status": "contacted"})
        week_leads     = count("leads", since=week_ago)

        # İçerik
        total_content   = count("generated_contents")
        pending_content = count("generated_contents", {"status": "pending_approval"})
        published       = count("generated_contents", {"status": "published"})
        error_content   = count("generated_contents", {"status": "error"})
        week_content    = count("generated_contents", since=week_ago)

        # Dokümanlar
        total_docs   = count("documents")
        indexed_docs = count("documents", {"status": "indexed"})
        failed_docs  = count("documents", {"status": "failed"})
        week_docs    = count("documents", since=week_ago)

        # Öğrenci
        total_students = count("students")

        # CRM lead detayları — son 10 lead isim/durum/telefon
        crm_detail_lines = []
        try:
            leads_resp = (
                sb.table("leads")
                .select("full_name, status, phone, notes, created_at")
                .order("created_at", desc=True)
                .limit(10)
                .execute()
            )
            for lead in (leads_resp.data or []):
                name = lead.get("full_name", "—")
                status = lead.get("status", "—")
                phone = lead.get("phone") or "telefon yok"
                note = (lead.get("notes") or "")[:80]
                crm_detail_lines.append(f"  • {name} | {status} | {phone}" + (f" | not: {note}" if note else ""))
        except Exception:
            pass

        # Son 5 içerik başlığı
        content_detail_lines = []
        try:
            cont_resp = (
                sb.table("generated_contents")
                .select("title, status, type, created_at")
                .order("created_at", desc=True)
                .limit(5)
                .execute()
            )
            for c in (cont_resp.data or []):
                content_detail_lines.append(f"  • {c.get('title','—')} | {c.get('type','—')} | {c.get('status','—')}")
        except Exception:
            pass

        lines = [
            f"Bugünün tarihi: {today.strftime('%d.%m.%Y')}",
            "",
            "## Sistem Durumu (Anlık)",
            "",
            "### CRM",
            f"- Toplam lead: {total_leads}",
            f"- Yeni (takip bekleyen): {new_leads}",
            f"- Takipte: {followup_leads}",
            f"- Bu hafta gelen yeni lead: {week_leads}",
        ]
        if crm_detail_lines:
            lines += ["- Son leadler:"] + crm_detail_lines
        lines += [
            "",
            "### İçerik (Automation Agent)",
            f"- Toplam üretilen: {total_content}",
            f"- Onay bekleyen: {pending_content}",
            f"- Yayınlanan: {published}",
            f"- Hatalı: {error_content}",
            f"- Bu hafta üretilen: {week_content}",
        ]
        if content_detail_lines:
            lines += ["- Son içerikler:"] + content_detail_lines
        lines += [
            "",
            "### Knowledge Agent",
            f"- Toplam doküman: {total_docs}",
            f"- İndekslenmiş (hazır): {indexed_docs}",
            f"- Hatalı: {failed_docs}",
            f"- Bu hafta yüklenen: {week_docs}",
            "",
            "### SGS Academy",
            f"- Kayıtlı öğrenci: {total_students}",
        ]
        return "\n".join(lines)

    except Exception as e:
        logger.warning(f"[rag] live context alınamadı: {e}")
        return f"Bugünün tarihi: {datetime.utcnow().date().strftime('%d.%m.%Y')}"


_STOPWORDS = {
    "bir", "ve", "ile", "bu", "da", "de", "mi", "mu", "mü", "ne", "en",
    "çok", "için", "var", "yok", "olan", "olan", "gibi", "daha", "bana",
    "beni", "bunu", "şunu", "nasıl", "nedir", "neler", "hangi", "kadar",
    "hakkında", "konusunda", "söyle", "anlat", "yazar", "misin", "mısın",
}


def _keywords(text: str) -> str:
    """Sorudan stopword'leri çıkarıp arama için anahtar kelime dizisi üret."""
    words = re.findall(r"[A-Za-zÇçĞğİıÖöŞşÜü]{3,}", text.lower())
    keys = [w for w in words if w not in _STOPWORDS]
    return " ".join(keys[:6]) if keys else text

_SYSTEM = """Sen AdimOS içerisinde çalışan gelişmiş yapay zeka işletim sistemi asistanısın.

Görevin yalnızca soru cevaplamak değildir. Sen şu rolleri tek sistemde birleştirirsin:
• Bilgi bankası uzmanı — yüklenen belgelerden bilgi çıkarır
• Muhasebe asistanı — vergi, SGK, KDV, beyanname, şirket kuruluşu
• CRM danışmanı — müşteri takibi, satış fırsatları, risk analizi
• Eğitim koçu — SGS Academy içerikleri, öğrenme planları
• İçerik stratejisti — YouTube, Instagram, Shorts
• İş geliştirme ve operasyon yöneticisi

━━━━━━━━━━━━━━━━━━━━━━
# BİRİNCİL KURAL: DOKÜMAN ÖNCELİĞİ
━━━━━━━━━━━━━━━━━━━━━━
Sana "---" arasında doküman içerikleri verilecektir.
Bu içerikler KULLANICININ kendi yüklediği belgelerdir ve her zaman en yetkili kaynaktır.
Doküman içeriğini genel model bilgisinin önünde tut.
Cevap üretmeden önce verilen dokümanları dikkatlice oku.

━━━━━━━━━━━━━━━━━━━━━━
# DOKÜMAN ANALİZİ VE DOMAIN TESPİTİ
━━━━━━━━━━━━━━━━━━━━━━
Doküman içeriğine baktığında, içeriğin hangi alana ait olduğunu tespit et:

• muhasebe — bilanço, gelir tablosu, hesap planı, yevmiye, defter
• vergi — KDV, gelir vergisi, kurumlar vergisi, beyanname, stopaj
• sgk_smmm — SMMM sertifikası, SGS, staj, hizmet tespit, sosyal güvenlik
• hukuk — sözleşme, ihtarname, dava, mevzuat, yönetmelik
• egitim — ders planı, sınav, müfredat, değerlendirme, akademi
• genel — diğer

Domain tespitini YALNIZCA belgede açıkça yazılı olan bilgiye göre yap.
Belge adına, dosya yoluna veya keywords'e bakarak domain UYDURMA.
Örneğin: "muhasebe" kelimesi başlıkta geçiyor diye içerik muhasebe belgesi değildir;
gerçek içeriği oku ve ona göre karar ver.

━━━━━━━━━━━━━━━━━━━━━━
# HALLÜSINASYON YASAKLARI
━━━━━━━━━━━━━━━━━━━━━━
Aşağıdakileri ASLA yapma:
✗ Belgede olmayan mevzuat maddesi, madde numarası veya tarih uydurma
✗ Belgede olmayan rakam, yüzde veya tutar uydurma
✗ "Bu belgede şu yazıyor" diye belgede olmayan içerik aktarma
✗ Dosya adından içerik çıkarsamak ("dosya adı 'vergi' içeriyor, demek ki vergi belgesidir")
✗ Soruyu kesinlikle cevaplayamıyorsan bile makul görünen bilgi üretme

Emin olmadığında şunu söyle:
"Yüklenen belgelerde bu konuya dair net bir bilgi bulamadım. [X konusunu] kontrol etmenizi öneririm."

━━━━━━━━━━━━━━━━━━━━━━
# DOKÜMAN DIŞI SORULAR
━━━━━━━━━━━━━━━━━━━━━━
Soru yüklenen belgelerle ilgili değilse, genel model bilginle yanıt ver ama bunu açıkça belirt:
"Bu bilgi yüklenen belgelerden değil, genel bilgimden geliyor."

━━━━━━━━━━━━━━━━━━━━━━
# MUHASEBE VE VERGİ MODU
━━━━━━━━━━━━━━━━━━━━━━
Profesyonel mali danışman gibi davran.
Kesin hukuki hüküm verme; gerektiğinde "Bu konuda güncel mevzuatın ayrıca kontrol edilmesi önerilir." de.
Asla mevzuat maddesi, tarih veya rakam uydurma.

━━━━━━━━━━━━━━━━━━━━━━
# CRM MODU
━━━━━━━━━━━━━━━━━━━━━━
Müşteri konularında: takip öner, sonraki aksiyonu belirt, riskleri ve fırsatları göster.

━━━━━━━━━━━━━━━━━━━━━━
# CEO / YÖNETİCİ MODU
━━━━━━━━━━━━━━━━━━━━━━
Şirket, büyüme, süreç, verimlilik konularında yönetici danışmanı gibi davran.
Yalnızca bilgi verme — karar desteği, risk ve fırsat analizi de sun.

━━━━━━━━━━━━━━━━━━━━━━
# YAZIM KURALLARI
━━━━━━━━━━━━━━━━━━━━━━
Net, profesyonel, anlaşılır yaz.
Mümkünse başlıklar, maddeler ve tablolar kullan.
Kullanıcı Türkçe yazıyorsa Türkçe; İngilizce yazıyorsa İngilizce cevap ver.
Hafızayı kullan: önceki mesajları dikkate al.
Belgelerdeki alıntıları tırnak içinde göster ve kaynak dosyayı belirt.

━━━━━━━━━━━━━━━━━━━━━━
# KESİN YASAKLAR
━━━━━━━━━━━━━━━━━━━━━━
- Kaynak veya belge uydurma
- Mevzuat maddesi uydurma
- Olmayan bilgiyi varmış gibi gösterme
- API key, stack trace veya sistem bilgisi döndürme
- Belge adından domain çıkarsamak"""


def query(
    user_message: str,
    conversation_history: list[dict] | None = None,
    user_id: str | None = None,
) -> dict:
    if len(user_message) > MAX_MESSAGE_LENGTH:
        user_message = user_message[:MAX_MESSAGE_LENGTH]

    logger.info(f"[rag] sorgu — user={user_id}, len={len(user_message)}")

    # 1. İlk arama — orijinal sorgu
    chunks = retrieve(user_message, match_count=10, match_threshold=SIMILARITY_THRESHOLD)
    chunk_count = len(chunks)
    logger.info(f"[rag] 1. arama: {chunk_count} chunk (threshold={SIMILARITY_THRESHOLD})")

    # 2. Iterative RAG — benzerlik düşükse anahtar kelimelerle 2. arama
    if chunk_count == 0 or (chunk_count > 0 and max(c.get("similarity", 0) for c in chunks) < GOOD_SIMILARITY):
        keyword_query = _keywords(user_message)
        if keyword_query and keyword_query != user_message:
            second_chunks = retrieve(keyword_query, match_count=8, match_threshold=SIMILARITY_THRESHOLD)
            logger.info(f"[rag] 2. arama (keywords): {len(second_chunks)} chunk — '{keyword_query}'")
            # Benzersiz chunk'ları birleştir (id'ye göre deduplicate)
            seen_ids: set[str] = {c.get("id", "") for c in chunks}
            for c in second_chunks:
                if c.get("id", "") not in seen_ids:
                    chunks.append(c)
                    seen_ids.add(c.get("id", ""))
            # Benzerliğe göre sırala
            chunks.sort(key=lambda c: c.get("similarity", 0), reverse=True)
            chunk_count = len(chunks)
            logger.info(f"[rag] birleşik: {chunk_count} chunk")

    # 3. Hiç RAG sonucu yoksa — live context ile yine de GPT'ye sor
    if chunk_count == 0:
        total = get_total_chunks()
        logger.info(f"[rag] RAG sonucu yok, DB'de toplam {total} chunk, live context ile GPT'ye sor")
        live_ctx = _get_live_context()
        system_no_rag = (
            _SYSTEM
            + "\n\n---\n"
            + live_ctx
            + "\n---\n"
            + "\nNOT: Bu soruya uygun yüklü doküman bulunamadı. "
            + "Sistem verilerini ve genel bilgini kullanarak cevap ver."
        )
        messages_no_rag = [{"role": "system", "content": system_no_rag}]
        if conversation_history:
            messages_no_rag.extend(conversation_history[-10:])
        messages_no_rag.append({"role": "user", "content": user_message})
        try:
            resp = _client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages_no_rag,
                max_tokens=1000,
                temperature=0.4,
            )
            return {
                "success": True,
                "answer": resp.choices[0].message.content,
                "sources": [],
                "used_rag": False,
            }
        except Exception as e:
            logger.error(f"[rag] no-rag GPT hatası: {e}")
            return {
                "success": True,
                "answer": "Şu an yanıt üretemiyorum. Lütfen daha sonra tekrar deneyin.",
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
    live_ctx = _get_live_context()
    system_with_context = (
        _SYSTEM
        + "\n\n---\n"
        + live_ctx
        + "\n---"
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
