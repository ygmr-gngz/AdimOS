-- Migration 010: konu_anlatimi tip kısıt + indeksleme denetim fonksiyonu
-- Tarih: 2026-07-08
-- Bu migration'ı Supabase SQL Editor'de çalıştır.

-- ── 1. video_jobs.type kısıtına konu_anlatimi ekle ───────────────
-- 009'da eklenen constraint'i genişlet
ALTER TABLE video_jobs DROP CONSTRAINT IF EXISTS video_jobs_type_check;
ALTER TABLE video_jobs
  ADD CONSTRAINT video_jobs_type_check
  CHECK (type IN ('quiz', 'lesson', 'konu_anlatimi', 'shorts', 'motivation', 'infographic', 'sgs_topic_video'));

-- ── 2. video_jobs'a topic ve lesson_name INDEX ─────────────────────
CREATE INDEX IF NOT EXISTS idx_video_jobs_topic
  ON video_jobs (topic)
  WHERE topic IS NOT NULL;

-- ── 3. İndeksleme durum görünümü ─────────────────────────────────
-- documents tablosunun indeksleme durumunu hızlı sorgulamak için
CREATE OR REPLACE VIEW documents_indexing_status AS
SELECT
  d.id,
  d.file_name,
  d.status,
  d.source_module,
  d.created_at,
  d.file_size,
  COUNT(c.id)                        AS chunk_count,
  COUNT(c.embedding)                 AS embedded_count,
  EXISTS (
    SELECT 1 FROM sgs_questions sq WHERE sq.document_id = d.id LIMIT 1
  )                                   AS topic_mapped,
  d.storage_path IS NOT NULL
    AND d.storage_path != ''          AS has_storage_path
FROM documents d
LEFT JOIN chunks c ON c.document_id = d.id
GROUP BY d.id, d.file_name, d.status, d.source_module, d.created_at, d.file_size, d.storage_path;
