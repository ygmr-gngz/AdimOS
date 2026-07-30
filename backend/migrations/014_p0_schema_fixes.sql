-- AdimOS Migration 014 — P0 şema drift düzeltmeleri
-- Supabase SQL Editor'da çalıştır.
-- 2026_07_29 migration'ının eksik bıraktığı kolonlar + CHECK kısıtları.
--
-- Çalıştırma sonrası doğrulama:
--   SELECT column_name, data_type FROM information_schema.columns
--   WHERE table_name = 'video_scenes' ORDER BY ordinal_position;

BEGIN;

-- ── video_jobs eksik kolonlar ────────────────────────────────────
ALTER TABLE public.video_jobs
  ADD COLUMN IF NOT EXISTS duration_tolerance_seconds  integer   DEFAULT 8,
  ADD COLUMN IF NOT EXISTS aspect_ratio                text,
  ADD COLUMN IF NOT EXISTS render_cost_usd             numeric,
  ADD COLUMN IF NOT EXISTS image_cost_usd              numeric;

-- ── video_jobs content_type CHECK kısıtı ────────────────────────
-- Kanonik 5 değer: master spec §P0-4
ALTER TABLE public.video_jobs
  DROP CONSTRAINT IF EXISTS video_jobs_content_type_check;
ALTER TABLE public.video_jobs
  ADD CONSTRAINT video_jobs_content_type_check
  CHECK (content_type IS NULL OR content_type IN (
    'konu_anlatimi', 'soru_cozum', 'reels_short', 'motivasyon', 'gorsel_post'
  ));

-- ── video_jobs content_track CHECK kısıtı ───────────────────────
ALTER TABLE public.video_jobs
  DROP CONSTRAINT IF EXISTS video_jobs_content_track_check;
ALTER TABLE public.video_jobs
  ADD CONSTRAINT video_jobs_content_track_check
  CHECK (content_track IS NULL OR content_track IN ('ogrenci', 'danisan'));

-- ── video_scenes eksik kolonlar ──────────────────────────────────
ALTER TABLE public.video_scenes
  ADD COLUMN IF NOT EXISTS status                  text    NOT NULL DEFAULT 'pending',
  ADD COLUMN IF NOT EXISTS audio_url               text,
  ADD COLUMN IF NOT EXISTS audio_duration_seconds  numeric,
  ADD COLUMN IF NOT EXISTS duration_seconds        numeric,
  ADD COLUMN IF NOT EXISTS spoken_text             text,
  ADD COLUMN IF NOT EXISTS captions                jsonb,
  ADD COLUMN IF NOT EXISTS image_asset_id          text,
  ADD COLUMN IF NOT EXISTS error_code              text,
  ADD COLUMN IF NOT EXISTS error_detail            jsonb;

-- ── video_scenes.status CHECK (tts_failed eklendi — 23514 fix) ──
ALTER TABLE public.video_scenes
  DROP CONSTRAINT IF EXISTS video_scenes_status_check;
ALTER TABLE public.video_scenes
  ADD CONSTRAINT video_scenes_status_check CHECK (status IN (
    'pending', 'narration_ready', 'tts_pending', 'tts_failed',
    'audio_ready', 'audio_invalid', 'visual_pending', 'visual_failed',
    'ready', 'skipped'
  ));

-- ── video_scenes.visual_source CHECK ────────────────────────────
ALTER TABLE public.video_scenes
  DROP CONSTRAINT IF EXISTS video_scenes_visual_source_check;
ALTER TABLE public.video_scenes
  ADD CONSTRAINT video_scenes_visual_source_check
  CHECK (visual_source IS NULL OR visual_source IN (
    'photo', 'card', 'table', 'journal', 'board', 'text_only'
  ));

-- ── video_scenes süre tutarlılık kısıtı ─────────────────────────
-- Hazır sahne için süre zorunlu ve pozitif
ALTER TABLE public.video_scenes
  DROP CONSTRAINT IF EXISTS video_scenes_duration_positive;
ALTER TABLE public.video_scenes
  ADD CONSTRAINT video_scenes_duration_positive
  CHECK (status <> 'ready' OR (duration_seconds IS NOT NULL AND duration_seconds > 0));

COMMIT;

-- PostgREST şema önbelleğini yenile (bu olmadan PGRST204 devam eder)
NOTIFY pgrst, 'reload schema';

-- ── Doğrulama sorguları ──────────────────────────────────────────
-- Aşağıdakileri ayrı ayrı çalıştırarak kontrol et:

-- 1. video_scenes yeni kolonlar
-- SELECT column_name, data_type, is_nullable, column_default
-- FROM information_schema.columns
-- WHERE table_name = 'video_scenes'
-- ORDER BY ordinal_position;

-- 2. CHECK kısıtları
-- SELECT constraint_name, check_clause
-- FROM information_schema.check_constraints
-- WHERE constraint_name LIKE 'video_%'
-- ORDER BY constraint_name;

-- 3. tts_failed değerini test et (hata vermemeli):
-- INSERT INTO video_scenes (job_id, scene_index, component, data, status)
-- VALUES ('00000000-0000-0000-0000-000000000000', 0, 'Test', '{}', 'tts_failed')
-- ON CONFLICT DO NOTHING;
-- DELETE FROM video_scenes WHERE job_id = '00000000-0000-0000-0000-000000000000';
