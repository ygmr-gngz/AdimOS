# FAZ 0 — Sistem Envanteri

**Tarih:** 2026-07-03  
**Versiyon:** 0.1.0  
**Platform:** Next.js 15 (Vercel) + FastAPI (Railway) + Supabase

---

## 1. Mimari Genel Bakış

```
Browser (React 19)
    │
    ├─► Vercel (Next.js 15.5) — frontend/web/
    │       Middleware: src/middleware.ts → /login redirect
    │
    └─► Railway (FastAPI 0.115 / uvicorn) — backend/app/
            │
            ├─► Supabase (PostgreSQL + Storage)
            ├─► OpenAI API (GPT-4o)
            ├─► Google Gemini API
            ├─► Meta Graph API (Instagram)
            └─► YouTube Data API v3
```

---

## 2. Backend — Route Envanteri (21 route)

| Route Prefix       | Dosya               | Auth | Açıklama                          |
|--------------------|---------------------|------|-----------------------------------|
| GET /health        | health.py           | ❌    | Servis sağlık kontrolü            |
| POST /webhooks     | webhooks.py         | ❌    | Meta/genel webhook alıcı          |
| /meta (GET/POST)   | meta_webhook.py     | ❌    | Meta verify token                  |
| /oauth             | oauth.py            | ❌    | OAuth callback (YouTube/Meta)      |
| /documents         | documents.py        | ✅    | Döküman yükleme ve listeleme      |
| /chat              | chat.py             | ✅    | AI sohbet (LangGraph)             |
| /voice             | voice.py            | ✅    | Ses tanıma/sentezi                |
| /agents            | agents.py           | ✅    | CEO Agent, otomasyon ajanlari      |
| /dashboard         | dashboard.py        | ✅    | Dashboard istatistikleri, brief    |
| /crm               | crm.py              | ✅    | Müşteri/lead yönetimi             |
| /academy           | academy.py          | ✅    | (Legacy) SGS academy              |
| /automation        | automation.py       | ✅    | İçerik otomasyon planları         |
| /content           | content.py          | ✅    | İçerik üretimi                    |
| /debug             | debug.py            | ✅    | Debug endpoint'leri               |
| /users             | users.py            | ✅    | Kullanıcı profilleri              |
| /sgs               | sgs.py              | ✅    | SGS PDF analiz, sorular, video     |
| /notifications     | notifications.py    | ✅    | Bildirimler                       |
| /social            | social.py           | ✅    | Instagram/sosyal medya            |
| /brand             | brand.py            | ✅    | Marka yönetimi                    |
| /video             | video.py            | ✅    | Video iş kuyruğu                  |
| /meta (protected)  | meta_webhook.py     | ✅    | Meta korumalı endpoint'ler        |

**Güvenlik:** 4 public + 17 protected route. Tüm korumalı route'lar `_protected = APIRouter(dependencies=[Depends(get_current_user)])` ile Supabase JWT doğrulama zorunlu kılıyor.

---

## 3. Frontend — Sayfa Envanteri (15 sayfa)

| Route          | Klasör/Dosya              | Açıklama                          |
|----------------|---------------------------|-----------------------------------|
| /login         | app/login/page.tsx         | Supabase email+şifre girişi       |
| /dashboard     | app/dashboard/            | Ana panel, istatistikler          |
| /academy       | app/academy/page.tsx       | SGS PDF yükleme, soru analizi     |
| /chat          | app/chat/page.tsx          | AI sohbet (LangGraph)             |
| /voice         | app/voice/page.tsx         | Ses arayüzü                       |
| /crm           | app/crm/page.tsx           | CRM / lead listesi                |
| /automation    | app/automation/page.tsx    | Otomasyon görev tablosu           |
| /content       | app/content/page.tsx       | İçerik üretimi                    |
| /instagram     | app/instagram/page.tsx     | Instagram DM yönetimi             |
| /reports       | app/reports/page.tsx       | CEO Agent günlük brief            |
| /video         | app/video/page.tsx         | Video iş kuyruğu, önizleme        |
| /knowledge     | (embedded in dashboard)    | Döküman bilgi tabanı              |
| /website       | app/website/page.tsx       | Web sitesi yönetimi               |
| /widget        | app/widget/page.tsx        | Embedded widget                   |
| /settings      | app/settings/page.tsx      | Kullanıcı ayarları                |

**Auth guard:** `frontend/web/src/middleware.ts` — tüm route'lar /login'e yönlendiriyor, supabase session cookie kontrolü yapıyor.

---

## 4. Veritabanı — Tablo Envanteri (Supabase/PostgreSQL)

| Tablo                  | Kullanım                                          |
|------------------------|---------------------------------------------------|
| `sgs_analyses`         | SGS PDF analiz sonuçları (JSONB: subjects, questions, video_plan) |
| `sgs_questions`        | Bireysel SGS soruları (lesson, topic, year, semester, options, answer) |
| `sgs_question_ranges`  | Soru aralığı tanımları (lesson, question_start/end) |
| `documents`            | Yüklenen dökümanlar (storage_path, mime_type, source_module) |
| `briefs`               | CEO Agent günlük brief'leri (content, created_at) |
| `video_jobs`           | Video render iş kuyruğu (status, scenes, tts_url) |
| `video_scenes`         | Video sahneleri (script, tts_url, duration)       |
| `leads`                | CRM müşteri/adayları                              |
| `user_profiles`        | Kullanıcı profilleri (Supabase auth user_id FK)   |
| `generated_contents`   | Üretilen içerikler (type, content, status)        |

---

## 5. Servisler ve Bağımlılıklar

### Backend Bağımlılıkları (requirements.txt)
| Paket                  | Sürüm       | Kullanım                         |
|------------------------|-------------|----------------------------------|
| fastapi                | 0.115.6     | Web framework                    |
| uvicorn[standard]      | 0.32.1      | ASGI server                      |
| supabase               | 2.10.0      | DB + Storage client              |
| httpx                  | 0.27.2      | Async HTTP (Supabase SDK)        |
| openai                 | 1.57.4      | GPT-4o API                       |
| google-generativeai    | 0.8.3       | Gemini API                       |
| langgraph              | 0.2.59      | AI agent orkestrasyon            |
| langchain              | 0.3.12      | LLM zinciri / araçlar            |
| pypdf                  | 5.1.0       | PDF metin çıkarma                |
| moviepy                | 1.0.3       | Video birleştirme (ffmpeg gerekli)|
| Pillow                 | 11.1.0      | Görsel işleme                    |
| apscheduler            | 3.10.4      | Görev zamanlama                  |
| loguru                 | 0.7.3       | Yapılandırılmış loglama          |
| pytest                 | 8.3.4       | Test framework                   |

### Frontend Bağımlılıkları (package.json)
| Paket                  | Sürüm       | Kullanım                         |
|------------------------|-------------|----------------------------------|
| next                   | 15.5.19     | React full-stack framework       |
| react                  | 19.x        | UI library                       |
| @supabase/ssr          | latest      | Supabase server-side auth        |
| axios                  | latest      | HTTP client (api-client.ts)      |
| react-hot-toast        | latest      | Bildirim toastları               |
| lucide-react           | latest      | İkon seti                        |

---

## 6. Ortam Değişkenleri

### Backend (Railway)
| Değişken                       | Açıklama                          | Kritik |
|--------------------------------|-----------------------------------|--------|
| `SUPABASE_URL`                 | Supabase proje URL'si             | ✅      |
| `SUPABASE_SERVICE_ROLE_KEY`    | Admin erişim (gizli kalmalı!)     | 🔴      |
| `OPENAI_API_KEY`               | OpenAI API                        | 🔴      |
| `GEMINI_API_KEY`               | Google Gemini API                 | 🔴      |
| `WEBHOOK_SECRET`               | Meta webhook imza doğrulama       | 🔴      |
| `META_ACCESS_TOKEN`            | Instagram Graph API               | 🔴      |
| `META_VERIFY_TOKEN`            | Meta webhook doğrulama            | 🔴      |
| `META_APP_ID`                  | Meta uygulama ID                  | ⚠️      |
| `META_APP_SECRET`              | Meta uygulama sırrı               | 🔴      |
| `INSTAGRAM_BUSINESS_ACCOUNT_ID`| IG hesap ID                       | ⚠️      |
| `YOUTUBE_CLIENT_ID`            | YouTube OAuth                     | ⚠️      |
| `YOUTUBE_CLIENT_SECRET`        | YouTube OAuth sırrı               | 🔴      |
| `YOUTUBE_REFRESH_TOKEN`        | YouTube uzun süreli token         | 🔴      |
| `ENVIRONMENT`                  | development / production          | ⚠️      |
| `REMOTION_URL`                 | Remotion render sunucusu URL'si   | ⚠️      |

### Frontend (Vercel env vars)
| Değişken                       | Açıklama                          | Güvenli? |
|--------------------------------|-----------------------------------|----------|
| `NEXT_PUBLIC_SUPABASE_URL`     | Supabase URL (public key)         | ✅ OK     |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY`| Supabase anon key (public key)    | ✅ OK     |
| `NEXT_PUBLIC_API_BASE_URL`     | Railway backend URL               | ✅ OK     |

---

## 7. Zamanlama (APScheduler)

| Görev           | Zaman  | Açıklama                              |
|-----------------|--------|---------------------------------------|
| `daily_brief`   | 08:00  | CEO Agent günlük özet oluşturur       |
| `followup_check`| 09:00  | CRM takip görev kontrolü              |

**Uyarı:** APScheduler main process içinde çalışıyor. Railway restart edilirse bir sonraki tetiklenme anına kadar çalışmaz — state belleğe bağlı.

---

## 8. Bilinen Sınırlamalar

- **Remotion render sunucusu** Railway'de deploy edilmemiş → video render 502 döner
- **moviepy** ffmpeg sisteme kurulu olmalı (Railway'de kontrol edilmeli)
- **Tek kullanıcı sistemi**: IDOR koruması yok — tüm kimlik doğrulanmış kullanıcılar birbirinin verilerine erişebilir
- **Rate limiting** yok — LLM endpoint'leri spam'e açık
- **No Sentry / error tracking** — production hataları sadece loglarla izleniyor
