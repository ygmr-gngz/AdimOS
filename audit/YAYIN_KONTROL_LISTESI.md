# FAZ 5 — Yayın Kontrol Listesi

**Tarih:** 2026-07-03  
**Hedef:** AdimOS v0.1.0 Production Readiness

---

## Backend (Railway)

### Ortam Değişkenleri
- [x] `SUPABASE_URL` — ayarlandı
- [x] `SUPABASE_SERVICE_ROLE_KEY` — ayarlandı
- [x] `OPENAI_API_KEY` — ayarlandı
- [x] `GEMINI_API_KEY` — ayarlandı
- [x] `WEBHOOK_SECRET` — ayarlandı
- [x] `META_ACCESS_TOKEN` — ayarlandı
- [x] `META_VERIFY_TOKEN` — ayarlandı
- [x] `INSTAGRAM_BUSINESS_ACCOUNT_ID` — ayarlandı
- [ ] `ENVIRONMENT=production` — **kontrol et**
- [ ] `REMOTION_URL` — ya gerçek Remotion URL ya da boş bırak

### Bağımlılıklar
- [x] Celery/Redis requirements'tan kaldırıldı
- [x] Duplicate httpx satırı kaldırıldı
- [ ] `ffmpeg` Railway container'a kurulu mu kontrol et

### API
- [x] Tüm protected endpoint'ler auth zorunlu
- [x] Dosya boyutu sınırı eklendi (50 MB, HTTP 413)
- [x] PDF dedup kontrolü (hem backend hem frontend)
- [ ] Rate limiting — **EKLENMEDİ** (sonraki sprint)
- [ ] IDOR (sahiplik) kontrolleri — **EKLENMEDİ** (sonraki sprint)
- [ ] Debug endpoint production'da kapat

### Zamanlama
- [x] APScheduler çalışıyor (daily_brief + followup_check)
- [ ] Railway restart sonrası scheduler otomatik başlıyor mu? — test et
- [ ] Opsiyonel: Railway Cron Job olarak taşı

---

## Frontend (Vercel)

### Ortam Değişkenleri (Vercel Dashboard)
- [x] `NEXT_PUBLIC_SUPABASE_URL` — ayarlandı
- [x] `NEXT_PUBLIC_SUPABASE_ANON_KEY` — ayarlandı
- [x] `NEXT_PUBLIC_API_BASE_URL` — Railway URL olarak ayarlandı (`https://adimos-production.up.railway.app`)
- [x] `.env.local` artık git'te yok (rm --cached)

### Güvenlik
- [x] Middleware tüm route'ları /login'e yönlendiriyor
- [x] API key'ler frontend'e asla gitmiyor
- [x] Supabase anon key public (tasarım gereği)

### UX
- [x] PDF dedup toast bildirimi
- [x] Video hata mesajı UI'da gösteriliyor
- [x] TTS ses dosyaları her sahnede çalınabiliyor
- [x] CEO Agent brief'leri Reports sayfasında görünüyor

---

## Supabase

### Veritabanı
- [ ] Row Level Security (RLS) politikaları — henüz yok, IDOR riski için önerilir
- [ ] `sgs_questions` indeksleri: `(lesson)`, `(year, semester)` — kontrol et
- [ ] `documents` tablosu `user_id` kolonu var mı?

### Storage
- [ ] Storage bucket erişim politikaları — public mi private mi?
- [ ] Eski/silinmiş analiz PDF'leri storage'dan temizleniyor mu?

---

## Bilinen Sınırlamalar (v0.1.0'da Kabul Edilenler)

| Sınırlama                          | Risk  | Plan                           |
|------------------------------------|-------|--------------------------------|
| Rate limiting yok                  | Orta  | Sonraki sprint                 |
| IDOR koruması yok                  | Düşük (tek kullanıcı) | Çok kullanıcılı olunca |
| Remotion servisi yok               | Düşük | TTS ses hazır, video opsiyonel |
| APScheduler main thread            | Düşük | Railway Cron'a taşınabilir     |
| localStorage token                 | Düşük (iç araç) | httpOnly cookie gelecekte |
| Sentry/error tracking yok          | Düşük | Sentry.io eklenebilir          |
| Sıfır test                         | Orta  | FAZ 4 test planı               |
| 30 sn frontend timeout             | Orta  | PDF analiz için artırılabilir  |

---

## Deploy Kontrol Adımları

1. `git push origin main` — her iki commit push edildi mi?
   - `faa8ce1` — SGS topic fix + video 502 fix
   - `f2d4dd8` — Audit FAZ1/FAZ2 fixes

2. Railway → auto-deploy tetiklendi mi kontrol et

3. Deploy sonrası:
   ```
   GET https://adimos-production.up.railway.app/health
   → {"status": "ok", "version": "0.1.0"}
   ```

4. SGS Academy → "Yeniden Sınıflandır" butonuna tıkla
   - Matematik/Finansal Muhasebe soruları artık doğru derse gitmeli

5. Hukuk PDF yeniden yükle (eğer daha önce parse edilmemişse)

6. Video → bir iş oluştur → "ready_for_review" durumunu gör (render hatası değil)

---

## Kısa Vadeli Yol Haritası

| Sprint | Madde                                        | Efor   |
|--------|----------------------------------------------|--------|
| v0.2   | slowapi rate limiting (LLM endpoint'leri)    | 2 saat |
| v0.2   | Debug endpoint production'da kapat           | 15 dk  |
| v0.2   | cryptography sürüm pinleme                   | 5 dk   |
| v0.3   | IDOR sahiplik kontrolleri                    | 4 saat |
| v0.3   | Supabase RLS politikaları                    | 2 saat |
| v0.4   | Sentry.io entegrasyonu                       | 1 saat |
| v0.4   | Railway Cron Job (scheduler yerine)          | 1 saat |
| v1.0   | Kapsamlı test suite (pytest)                 | 2 gün  |
