-- Migration 009: Video Pipeline V2 — yeni durumlar, arşiv ve infografik desteği
-- Tarih: 2026-07-05
-- Bu migration'ı Supabase SQL Editor'de çalıştır.

-- ── 1. Yeni status değerleri ──────────────────────────────────
-- Supabase'de status TEXT ise doğrudan geçerli; enum ise alter type gerekir.
-- video_jobs.status TEXT sütunu olduğundan ek işlem gerekmez.
-- Belgeleme amaçlı yorumlar:
--   warmup_pinging  : Remotion Railway App Sleeping'den uyanıyor, geçici durum
--   archived        : Temizlik tarafından arşivlendi, artık aktif değil

-- ── 2. archived_at + infographic_template sütunları ─────────
ALTER TABLE video_jobs
  ADD COLUMN IF NOT EXISTS archived_at          TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS infographic_template TEXT;

-- ── 2b. type constraint — infographic ve motivation eklenir ──
-- Mevcut constraint'i kaldır, genişletilmişini ekle
ALTER TABLE video_jobs DROP CONSTRAINT IF EXISTS video_jobs_type_check;
ALTER TABLE video_jobs
  ADD CONSTRAINT video_jobs_type_check
  CHECK (type IN ('quiz', 'lesson', 'shorts', 'motivation', 'infographic'));

-- ── 3. İnfografik kısayolu için yeni indeks ──────────────────
CREATE INDEX IF NOT EXISTS idx_video_jobs_type_status
  ON video_jobs (type, status);

CREATE INDEX IF NOT EXISTS idx_video_jobs_archived_at
  ON video_jobs (archived_at)
  WHERE archived_at IS NOT NULL;

-- ── 4. Arşivleme kolaylığı için view ─────────────────────────
CREATE OR REPLACE VIEW video_jobs_active AS
  SELECT *
  FROM video_jobs
  WHERE status NOT IN ('archived', 'rejected')
  ORDER BY created_at DESC;

-- ── 5. Warmup_pinging takılı kalma kontrolü için yorum ───────
-- Cron job her Pazartesi 03:00'da şu durumdakileri arşivler:
--   - 4+ saat önce güncellenen: pending, scripting, tts_generating, warmup_pinging, rendering
--   - 7+ gün önce güncellenen: failed
-- Bu mantık backend/app/modules/automation/scheduler.py'de _task_video_cleanup olarak uygulandı.
  