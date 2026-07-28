-- AdimOS video_jobs tablo genişletme migrasyonu
-- Supabase SQL Editor'da çalıştır, ardından NOTIFY satırını da çalıştır.
-- v2.1 Blokaj #1 — PGRST204 fix

BEGIN;

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
  ADD COLUMN IF NOT EXISTS render_id                   text,
  ADD COLUMN IF NOT EXISTS serve_url                   text,
  ADD COLUMN IF NOT EXISTS approved_by                 text,
  ADD COLUMN IF NOT EXISTS approved_at                 timestamptz;

CREATE UNIQUE INDEX IF NOT EXISTS video_jobs_idempotency_active
  ON public.video_jobs (idempotency_key)
  WHERE status IN ('queued', 'rendering');

CREATE INDEX IF NOT EXISTS video_jobs_status_created
  ON public.video_jobs (status, created_at DESC);

COMMIT;

-- PostgREST şema önbelleğini yenile (bu olmadan hata devam eder)
NOTIFY pgrst, 'reload schema';

-- Doğrulama: aşağıdaki sorgu yeni kolonları göstermeli
-- SELECT column_name, data_type FROM information_schema.columns
-- WHERE table_name = 'video_jobs' ORDER BY ordinal_position;
