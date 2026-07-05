# AdimOS — Yayılım Tablosu (GÖREV 0)

Tarih: 2026-07-05  
Repo HEAD: `65fa2a6` (fix: Remotion railway.json — healthcheck /health, restart policy)

---

## Bileşen Durumu

| Bileşen | Beklenen Commit | Kontrol Yöntemi | Durum |
|---------|----------------|-----------------|-------|
| **Vercel (frontend)** | `65fa2a6` | Vercel Dashboard → son deployment → Commit SHA | ⬜ DOĞRULANMADI |
| **Railway API (backend)** | `65fa2a6` | Railway → adimos-production → Deployments → en son | ⬜ DOĞRULANMADI |
| **Railway Remotion** | `65fa2a6` | Railway → motivated-generosity-production → Deployments | ⬜ DOĞRULANMADI |
| **Supabase migration 009** | `video_jobs_type_check` + `status_check` güncel | Supabase → SQL: `SELECT conname, consrc FROM pg_constraint WHERE conname LIKE 'video_jobs_%';` | ✅ UYGULANMIŞ (kullanıcı onayladı) |

---

## Supabase Constraint Doğrulama SQL'i

```sql
SELECT conname, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conname IN ('video_jobs_type_check', 'video_jobs_status_check');
```

Beklenen çıktı:
- `video_jobs_type_check`: `CHECK (type IN ('quiz', 'lesson', 'shorts', 'motivation', 'infographic'))`
- `video_jobs_status_check`: `CHECK (status IN ('draft', 'pending', 'scripting', 'tts_generating', 'warmup_pinging', 'rendering', 'ready_for_review', 'approved', 'queued_for_publishing', 'scheduled', 'published', 'rejected', 'failed', 'archived'))`

---

## Bu Oturumda Yapılan Düzeltmeler

| # | Sorun | Dosya | Değişiklik | Kanıt |
|---|-------|-------|-----------|-------|
| SORUN 1 | Agent Ofisi `replace` crash | `frontend/web/src/app/agents/page.tsx:55` | `run.agent_type.replace(...)` → `(run.agent_type ?? '').replace(...)` | Commit hash |
| SORUN 3a | Motivation video yanlış composition | `remotion/src/server/index.ts:77` | Sabit `'QuizVideo'` → video_type'a göre dispatch | Commit hash |
| SORUN 3b | warmup_pinging watchdog dışında | `backend/app/api/routes/video.py:watchdog` | `warmup_pinging` status eklendi | Commit hash |
| SORUN 2 | Infographic Remotion render yok | `backend/app/api/routes/video.py:infographic` | Shortcut kaldırıldı, `_run_remotion_render` ile render tetikleniyor | Commit hash |
| SORUN 4 | SplitQuizScene şablonu | `remotion/src/scenes/SplitQuizScene.tsx` | Commit `8e3d41f`'te yeniden tasarlandı | Commit logda görülür |

---

## Canlı Test Protokolü (Düzeltmeler Deploy Sonrası)

### SORUN 1 — Agent Ofisi Crash
```
1. agents sayfasını aç
2. API'de kasıtlı agent_type=null olan kayıt olsa bile sayfa çökmemeli
3. Beklenen: agent_type boş string olarak gösterilir, hata yoktur
```

### SORUN 3 — Motivasyon Video
```
1. /video sayfasında "Motivasyon" tipi video oluştur
2. Status: pending → scripting → tts_generating → warmup_pinging → rendering
3. Remotion callback gelince: ready_for_review + video_url dolu
4. Kanıt: video_url alanı dolu, video oynatılabilir
```

### SORUN 2 — Infografik
```
1. /video sayfasında "İnfografik" tipi oluştur
2. Status: pending → scripting → warmup_pinging → rendering
3. Remotion callback: ready_for_review + video_url dolu
4. Kanıt: video_url alanı dolu
```

### SORUN 4 — Quiz Şablonu
```
1. Yeni quiz video oluştur (SGS soruları ile)
2. Remotion render sonucu: SplitQuizScene — SOL soru (55%), SAĞ çözüm (45%), beyaz arka plan
3. Kanıt: video_url'deki video yeni tasarımı gösteriyor
```

---

## Notlar

- Remotion Railway servisi serverless KAPALI olmalı (varsayılan)
- `BACKEND_URL` env var Railway Remotion servisinde tanımlı olmalı (render-callback için)
- `REMOTION_URL` env var Railway backend'de `https://motivated-generosity-production.up.railway.app` olmalı
