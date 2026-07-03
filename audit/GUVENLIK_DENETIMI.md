# FAZ 2 — Güvenlik Denetimi

**Tarih:** 2026-07-03  
**Metodoloji:** OWASP Top 10 + API Security Top 10

---

## Özet

| Kategori              | Durum  | Risk  |
|-----------------------|--------|-------|
| Kimlik Doğrulama      | ✅ İYİ  | Düşük |
| Yetkilendirme (IDOR)  | ⚠️ EKSİK| Orta  |
| Giriş Doğrulama       | ⚠️ KISMÎ| Orta  |
| Dosya Yükleme         | ✅ İYİ  | Düşük |
| CORS                  | ✅ İYİ  | Düşük |
| Sır Yönetimi          | ✅ İYİ  | Düşük |
| Rate Limiting         | ❌ YOK  | Yüksek|
| Token Depolama        | ⚠️ ORTA | Orta  |
| SQL Injection         | ✅ İYİ  | Düşük |
| Webhook Güvenliği     | ✅ İYİ  | Düşük |

---

## G-01 — Kimlik Doğrulama ✅ İYİ

**Auth Flow:**
1. Browser → `supabase.auth.signInWithPassword(email, password)`
2. Supabase JWT token → `AuthContext` → `localStorage.adimos_token`
3. Her API isteği → `Authorization: Bearer <token>` header
4. FastAPI `get_current_user` → Supabase ile token doğrulama

**Değerlendirme:** Güçlü. Supabase JWT RSA imzalı, kısa süre geçerli. Tüm korumalı route'lar `_protected` router altında.

**Kalan Risk:** Token localStorage'da → XSS ile çalınabilir.  
**İç araç için:** Kabul edilebilir.  
**Genel kullanıma açılacaksa:** httpOnly cookie'ye geçilmeli.

---

## G-02 — Yetkilendirme / IDOR ⚠️ EKSİK

**Sorun:** Herhangi bir kimlik doğrulanmış kullanıcı, başka bir kullanıcının verilerine UUID bilerek erişebilir.

**Örnekler:**
- `GET /api/v1/sgs/analysis/{analysis_id}` — sahiplik kontrolü yok
- `GET /api/v1/documents/{document_id}` — sahiplik kontrolü yok
- `GET /api/v1/video/jobs/{job_id}` — sahiplik kontrolü yok

**Mevcut Durum:** Sistem şu an tek kullanıcı / tek şirket. Birden fazla kullanıcı eklenmeden önce mutlaka düzeltilmeli.

**Çözüm Şablonu:**
```python
# Her endpoint'te:
analysis = get_analysis(analysis_id)
if not analysis or analysis.get("user_id") != current_user["id"]:
    raise HTTPException(status_code=404)
```

**Supabase Row Level Security (RLS)** de alternatif olarak değerlendirilebilir.

---

## G-03 — Giriş Doğrulama ⚠️ KISMÎ

**İyi olanlar:**
- PDF extension kontrolü (sadece `.pdf`) — `sgs.py:36`
- Minimum boyut kontrolü (< 500 bytes) — `sgs.py:41`
- Maksimum boyut kontrolü 50 MB — `sgs.py:43` ✅ (bu session'da eklendi)

**Eksik:**
- `document_type`, `year`, `semester` Form alanları için doğrulama yok
- CRM lead verilerinde özel karakter sanitizasyonu yok (ama Supabase parametrik sorgu kullandığı için SQL injection riski yok)
- `document_id` UUID formatı doğrulanmıyor (Supabase hatalı format için 400 döndürüyor, yeterli)

---

## G-04 — Dosya Yükleme ✅ İYİ

- ✅ Sadece PDF kabul ediliyor (SGS endpoint'te extension kontrolü)
- ✅ Dosya içeriği MIME type ile değil, extension ile kontrol ediliyor
- ✅ 50 MB üst sınır eklendi (bu session'da)
- ✅ Dosyalar Supabase Storage'a atılıyor, doğrudan sunucuya değil
- ⚠️ `/documents` endpoint'te sadece boyut sınırı var, MIME kontrolü yok (güvenilir iç ortam için kabul edilebilir)

---

## G-05 — CORS Yapılandırması ✅ İYİ

```python
allow_origins=[
    "http://localhost:3000",
    "https://adim-os-web.vercel.app",
    "https://adimos-production.up.railway.app"
]
```

Dar liste. `"*"` yok. `allow_credentials=True` + dar `allow_origins` kombinasyonu güvenli.

---

## G-06 — Sır/API Key Yönetimi ✅ İYİ

- ✅ `SUPABASE_SERVICE_ROLE_KEY` sadece backend Railway env var
- ✅ `OPENAI_API_KEY` sadece backend Railway env var
- ✅ `GEMINI_API_KEY` sadece backend Railway env var
- ✅ Frontend sadece public Supabase key (`NEXT_PUBLIC_SUPABASE_ANON_KEY`) kullanıyor
- ✅ `.env.local` git takibinden çıkarıldı (bu session'da)
- ✅ `.gitignore`'a `.env.local` eklendi

---

## G-07 — Rate Limiting ❌ YOK

**Risk:** Yüksek (maliyet riski)

**Sorun:** Kimlik doğrulanmış kullanıcı:
- `/sgs/analyze` — PDF başına GPT-4o çağrısı (pahalı)
- `/chat` — sınırsız GPT-4o sorgusu
- `/voice` — sınırsız TTS/STT
- `/content` — sınırsız içerik üretimi

**Çözüm (Railway'de):**
```bash
pip install slowapi
```

```python
# main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# sgs.py
@router.post("/analyze")
@limiter.limit("10/hour")
async def analyze_pdf(request: Request, ...):
```

---

## G-08 — Webhook Güvenliği ✅ İYİ

`meta_webhook.py` — Meta `X-Hub-Signature-256` imza doğrulaması mevcut (`WEBHOOK_SECRET` ile HMAC-SHA256 kontrolü).

---

## G-09 — SQL Injection ✅ İYİ

Supabase Python client parametrik sorgular kullanıyor:
```python
supabase.table("sgs_questions").select("*").eq("lesson", lesson).execute()
```
ORM/parametrik sorgu → SQL injection riski yok.

---

## G-10 — Debug Endpoint ⚠️ DİKKAT

`/api/v1/debug` endpoint'i auth arkasında ama production'da kapatılmalı veya `ENVIRONMENT != "production"` kontrolü eklenmeli.

```python
# debug.py başına ekle:
if settings.ENVIRONMENT == "production":
    raise HTTPException(status_code=404)
```

---

## Eylem Listesi (Öncelik Sırasına Göre)

| Öncelik | Madde                                      | Efor  |
|---------|---------------------------------------------|-------|
| 🔴 1    | Rate limiting (slowapi) ekle                | 2 saat|
| 🔴 2    | IDOR: sahiplik kontrolü (user_id check)     | 4 saat|
| ⚠️ 3    | Debug endpoint production'da kapat          | 15 dk |
| ⚠️ 4    | Document upload için MIME type kontrolü     | 30 dk |
| 💡 5    | httpOnly cookie auth (gelecek sprint)       | 1 gün |
