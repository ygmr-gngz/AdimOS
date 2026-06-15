# Deploy Rehberi

## Genel Mimari

```
Frontend  → Vercel   (Next.js)
Backend   → Railway  (FastAPI + Docker)
Veritabanı→ Supabase (PostgreSQL + pgvector + Storage)
```

---

## 1. Supabase Kurulumu

1. [supabase.com](https://supabase.com) → Yeni proje oluştur
2. SQL Editör → `docs/03-database.md`'deki SQL'leri sırasıyla çalıştır
3. Storage → `documents` ve `audio` bucket'larını oluştur (Public: kapalı)
4. Settings → API → şu değerleri kopyala:
   - `Project URL` → `SUPABASE_URL` ve `NEXT_PUBLIC_SUPABASE_URL`
   - `anon public` key → `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `service_role` key → `SUPABASE_SERVICE_ROLE_KEY`

---

## 2. Railway — Backend Deploy

1. [railway.app](https://railway.app) → New Project → Deploy from GitHub
2. `backend/` klasörünü seç
3. Railway Dockerfile'ı otomatik bulur (`infrastructure/railway/railway.json`)
4. Environment Variables ekle:

```env
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...
OPENAI_API_KEY=sk-...
ENVIRONMENT=production
LOG_LEVEL=INFO
YOUTUBE_REFRESH_TOKEN=...
META_APP_ID=...
META_APP_SECRET=...
META_ACCESS_TOKEN=...
INSTAGRAM_BUSINESS_ACCOUNT_ID=...
```

5. Deploy → Railway URL oluşur: `https://adimos-api.railway.app`
6. Sağlık kontrolü: `https://adimos-api.railway.app/health` → `{"status":"ok"}`

---

## 3. Vercel — Frontend Deploy

1. [vercel.com](https://vercel.com) → New Project → Import from GitHub
2. `frontend/web/` klasörünü seç
3. Framework: Next.js (otomatik algılar)
4. Environment Variables ekle:

```env
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
NEXT_PUBLIC_API_BASE_URL=https://adimos-api.railway.app
```

5. Deploy → Vercel URL oluşur: `https://adimos.vercel.app`

---

## 4. CORS Güncelleme

Backend `main.py`'da Vercel URL'ini ekle (zaten mevcut):

```python
allow_origins=[
    "http://localhost:3000",
    "https://adimos.vercel.app",
]
```

---

## 5. YouTube OAuth Kurulumu

1. [Google Cloud Console](https://console.cloud.google.com) → Yeni proje
2. YouTube Data API v3 → Etkinleştir
3. OAuth 2.0 Client ID oluştur
4. Authorized redirect URI ekle:
   ```
   https://adimos-api.railway.app/api/v1/auth/youtube/callback
   ```
5. OAuth akışını bir kere çalıştır → `refresh_token` al → Railway env'e ekle

---

## 6. Instagram (Meta Graph API) Kurulumu

1. [Meta for Developers](https://developers.facebook.com) → Yeni uygulama
2. Instagram Graph API → Ekle
3. Business hesabı bağla
4. Access Token al → Railway env'e ekle

---

## Kontrol Listesi

- [ ] Supabase tabloları oluşturuldu
- [ ] pgvector extension etkinleştirildi
- [ ] Storage buckets oluşturuldu
- [ ] Railway deploy başarılı (`/health` endpoint yanıt veriyor)
- [ ] Vercel deploy başarılı (dashboard açılıyor)
- [ ] Frontend → Backend bağlantısı çalışıyor
- [ ] Supabase auth çalışıyor (giriş yapılabiliyor)
- [ ] YouTube OAuth tamamlandı
- [ ] Instagram token alındı
