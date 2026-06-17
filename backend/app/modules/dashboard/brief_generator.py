import logging
from datetime import date
from openai import OpenAI
from app.core.config import settings
from app.db.repositories.leads_repo import get_leads
from app.db.repositories.students_repo import get_students
from app.db.repositories.documents_repo import get_documents
from app.db.repositories.generated_contents_repo import list_contents
from app.db.repositories.briefs_repo import create_brief

_client = OpenAI(api_key=settings.OPENAI_API_KEY)
logger = logging.getLogger(__name__)


def _safe(fn):
    try:
        return fn()
    except Exception:
        return []


def generate_daily_brief() -> dict:
    today = date.today().strftime("%d.%m.%Y")

    leads     = _safe(get_leads)
    students  = _safe(get_students)
    documents = _safe(get_documents)
    contents  = _safe(list_contents)

    new_leads      = [l for l in leads if l.get("status") == "new"]
    followup_leads = [l for l in leads if l.get("status") == "contacted"]
    indexed_docs   = [d for d in documents if d.get("status") == "indexed"]
    failed_docs    = [d for d in documents if d.get("status") == "failed"]
    processing_docs = [d for d in documents if d.get("status") == "processing"]
    pending_cnt    = sum(1 for c in contents if c.get("status") == "pending_approval")
    error_cnt      = sum(1 for c in contents if c.get("status") in ("error", "failed"))
    published_cnt  = sum(1 for c in contents if c.get("status") == "published")
    generating_cnt = sum(1 for c in contents if c.get("status") == "generating")

    type_counts: dict[str, int] = {}
    for c in contents:
        t = c.get("type", "bilinmeyen")
        type_counts[t] = type_counts.get(t, 0) + 1

    content_summary = (
        ", ".join(f"{v} {k}" for k, v in type_counts.items())
        if type_counts else "henüz içerik yok"
    )

    # Agent durumları (metin özeti)
    k_status = (
        f"HATA ({failed_docs} hatalı belge)" if failed_docs else
        f"İŞLENİYOR ({len(processing_docs)} belge sırada)" if processing_docs else
        f"HAZIR ({len(indexed_docs)} belge indekslenmiş)"
    )
    a_status = (
        f"ÜRETİYOR ({generating_cnt} içerik)" if generating_cnt else
        f"UYARI ({error_cnt} hatalı içerik)" if error_cnt else
        "HAZIR"
    )
    c_status = f"{len(new_leads)} yeni · {len(followup_leads)} takipte · toplam {len(leads)}"

    prompt = f"""Sen Adım Müşavir AI işletim sistemi CEO Agentısın. Bugün {today} tarihli günlük özeti hazırla.

SİSTEM VERİLERİ:

CRM Agent: {c_status}
Knowledge Agent: {k_status}
Automation Agent: {a_status}
  - Üretilen: {content_summary}
  - Onay bekleyen: {pending_cnt} · Hata: {error_cnt} · Yayında: {published_cnt}
Öğrenci: {len(students)} kayıtlı

ŞU FORMATI KULLAN (Markdown, başka format kullanma):

## 📊 Günlük CEO Özeti — {today}

### 👥 CRM Agent
[lead durumu ve takip önerileri]

### 🧠 Knowledge Agent
[belge durumu — hata varsa ne yapılmalı]

### 🎬 Automation Agent
[içerik üretim durumu — hangi tip içerikler üretilmeli, öncelik sırası]

### ✅ Günlük Öneriler
1. [CRM ile ilgili aksiyon]
2. [Knowledge ile ilgili aksiyon]
3. [İçerik ile ilgili aksiyon]
4-5. [Varsa diğer öncelikler]

---
*AdimOS CEO Agent — {today}*

Türkçe yaz. Yönetici özeti tarzında, net ve kısa. Her bölüm 2-3 cümle."""

    try:
        response = _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=900,
            temperature=0.3,
        )
        content_text = response.choices[0].message.content
        logger.info("[ceo] günlük özet üretildi")
    except Exception as e:
        logger.error(f"[ceo] özet üretim hatası: {e}")
        content_text = f"""## Günlük CEO Özeti — {today}

### 👥 CRM Agent
{len(new_leads)} yeni lead, {len(followup_leads)} takip bekliyor, toplam {len(leads)} lead.

### 🧠 Knowledge Agent
{k_status}

### 🎬 Automation Agent
{a_status} — {content_summary}

### ✅ Günlük Öneriler
1. Yeni leadleri takip et.
2. Hatalı dokümanları yeniden işle.
3. İçerik üretimini kontrol et.

---
*AdimOS CEO Agent — {today} (OpenAI bağlantısı yok — ham özet)*"""

    return create_brief("Günlük CEO Özeti", content_text, "daily_brief")
