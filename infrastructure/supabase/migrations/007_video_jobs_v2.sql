-- Migration 007: video_jobs tablosuna maliyet ve payload alanları ekle
-- Tarih: 2026-07-04
-- Bu migration'ı Supabase SQL Editor'de çalıştır.

-- video_jobs tablosu yeni sütunlar
ALTER TABLE video_jobs
  ADD COLUMN IF NOT EXISTS description        TEXT,
  ADD COLUMN IF NOT EXISTS payload_json       JSONB,
  ADD COLUMN IF NOT EXISTS cost_tts_chars     INTEGER    DEFAULT 0,
  ADD COLUMN IF NOT EXISTS cost_tts_usd       NUMERIC(10,6),
  ADD COLUMN IF NOT EXISTS cost_llm_usd       NUMERIC(10,6),
  ADD COLUMN IF NOT EXISTS cost_total_usd_est NUMERIC(10,6),
  ADD COLUMN IF NOT EXISTS tts_provider       TEXT       DEFAULT 'openai',
  ADD COLUMN IF NOT EXISTS storage_path       TEXT,
  ADD COLUMN IF NOT EXISTS file_size_bytes    BIGINT,
  ADD COLUMN IF NOT EXISTS duration_seconds   FLOAT,
  ADD COLUMN IF NOT EXISTS error_message      TEXT;

-- Atomik iş sahiplenme fonksiyonu (ileride DB-backed worker için)
-- İki worker aynı anda aynı işi almasın diye SKIP LOCKED kullanır.
CREATE OR REPLACE FUNCTION claim_next_video_job()
RETURNS SETOF video_jobs AS $$
  UPDATE video_jobs
  SET status     = 'scripting',
      updated_at = NOW()
  WHERE id = (
    SELECT id FROM video_jobs
    WHERE status = 'pending'
    ORDER BY created_at ASC
    LIMIT 1
    FOR UPDATE SKIP LOCKED
  )
  RETURNING *;
$$ LANGUAGE SQL;

-- İndeksler
CREATE INDEX IF NOT EXISTS idx_video_jobs_status     ON video_jobs (status);
CREATE INDEX IF NOT EXISTS idx_video_jobs_created_at ON video_jobs (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_video_scenes_job_id   ON video_scenes (job_id);
