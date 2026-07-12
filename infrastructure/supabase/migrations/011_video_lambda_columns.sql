-- Migration 011: video_jobs Lambda render kolonları
-- Tarih: 2026-07-12
-- Supabase SQL Editor'de çalıştır.

-- ── Lambda render takip kolonları ────────────────────────────────
ALTER TABLE video_jobs
  ADD COLUMN IF NOT EXISTS composition_id     TEXT,
  ADD COLUMN IF NOT EXISTS render_id          TEXT,
  ADD COLUMN IF NOT EXISTS bucket_name        TEXT,
  ADD COLUMN IF NOT EXISTS cost_lambda_usd    NUMERIC(10, 6),
  ADD COLUMN IF NOT EXISTS render_progress_pct SMALLINT DEFAULT 0
    CHECK (render_progress_pct BETWEEN 0 AND 100);

-- ── İndeksler ────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_video_jobs_render_id
  ON video_jobs (render_id)
  WHERE render_id IS NOT NULL;

-- ── Açıklamalar ──────────────────────────────────────────────────
COMMENT ON COLUMN video_jobs.composition_id      IS 'Remotion composition ID (QuizVideo, LessonVideoDemo, vs.)';
COMMENT ON COLUMN video_jobs.render_id           IS 'Remotion Lambda renderId — getRenderProgress için';
COMMENT ON COLUMN video_jobs.bucket_name         IS 'Lambda S3 bucket adı (render çıktısı için)';
COMMENT ON COLUMN video_jobs.cost_lambda_usd     IS 'Lambda render maliyeti (USD) — getRenderProgress.costs';
COMMENT ON COLUMN video_jobs.render_progress_pct IS 'Lambda ilerleme yüzdesi 0-100 (callback ile güncellenir)';
