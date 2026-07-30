-- Migration 012: kanonik tip adları + şema düzeltmeleri
-- Tarih: 2026-07-29
-- Supabase SQL Editor'de çalıştır.

BEGIN;

-- ── 1. type CHECK kısıtı — kanonik adlar eklendi ─────────────────────
-- 010'da 'quiz', 'lesson', 'konu_anlatimi', 'shorts', 'motivation', 'infographic', 'sgs_topic_video' vardı.
-- Yeni kanonik adlar: soru_cozum, reels_short, gorsel_post, motivasyon
ALTER TABLE video_jobs DROP CONSTRAINT IF EXISTS video_jobs_type_check;
ALTER TABLE video_jobs
  ADD CONSTRAINT video_jobs_type_check CHECK (
    type IN (
      -- Kanonik adlar (yeni)
      'konu_anlatimi',
      'soru_cozum',
      'reels_short',
      'motivasyon',
      'gorsel_post',
      -- Eski adlar — DB'de kayıtlı eski işler için geriye dönük uyumluluk
      'quiz',
      'lesson',
      'shorts',
      'motivation',
      'infographic',
      'sgs_topic_video',
      'educational_reel',
      'motivation_reel'
    )
  );

-- ── 2. render_cost_usd eksik sütun — cost_lambda_usd zaten var (011)
--     Backend kod cost_lambda_usd kullanacak şekilde düzeltildi.
--     Bu satır yalnızca eski kayıtlar için bir alias view'ı değil,
--     sütun adının belgesi olarak bırakılıyor.
-- NOT: video.py'de render_cost_usd → cost_lambda_usd olarak düzeltildi.

-- ── 3. Idempotency partial index — 'queued' geçersiz statü düzeltildi
DROP INDEX IF EXISTS video_jobs_idempotency_active;
CREATE UNIQUE INDEX IF NOT EXISTS video_jobs_idempotency_active
  ON public.video_jobs (idempotency_key)
  WHERE status IN ('pending', 'scripting', 'tts_generating', 'rendering', 'warmup_pinging');

-- ── 4. Eksik sütunlar — 2026_07_29 backend migration'ının yerine geçer
--     (o migration Supabase'de çalıştırılmadıysa bu tamamlar)
ALTER TABLE public.video_jobs
  ADD COLUMN IF NOT EXISTS error_code                  text,
  ADD COLUMN IF NOT EXISTS error_stage                 text,
  ADD COLUMN IF NOT EXISTS retryable                   boolean,
  ADD COLUMN IF NOT EXISTS user_message                text,
  ADD COLUMN IF NOT EXISTS admin_detail                jsonb          DEFAULT '{}'::jsonb,
  ADD COLUMN IF NOT EXISTS quality_report              jsonb,
  ADD COLUMN IF NOT EXISTS postcheck_report            jsonb,
  ADD COLUMN IF NOT EXISTS publish_package             jsonb,
  ADD COLUMN IF NOT EXISTS idempotency_key             text,
  ADD COLUMN IF NOT EXISTS storyboard_hash             text,
  ADD COLUMN IF NOT EXISTS requested_duration_seconds  integer,
  ADD COLUMN IF NOT EXISTS actual_duration_seconds     numeric,
  ADD COLUMN IF NOT EXISTS trace_id                    text,
  ADD COLUMN IF NOT EXISTS serve_url                   text,
  ADD COLUMN IF NOT EXISTS approved_by                 text,
  ADD COLUMN IF NOT EXISTS approved_at                 timestamptz;

-- ── 5. İndeksler
CREATE INDEX IF NOT EXISTS video_jobs_status_created
  ON public.video_jobs (status, created_at DESC);

COMMIT;

-- PostgREST şema önbelleğini yenile
NOTIFY pgrst, 'reload schema';

-- Doğrulama:
-- SELECT column_name, data_type FROM information_schema.columns
-- WHERE table_name = 'video_jobs' ORDER BY ordinal_position;
