-- Migration 013: content_track + visual_source
-- Tarih: 2026-07-30
-- Supabase SQL Editor'de çalıştır.

BEGIN;

-- ── 1. video_jobs.content_track ──────────────────────────────
-- Hangi kitle hattı: 'ogrenci' (SGS/SMMM adayı) veya 'danisan' (KOBİ/esnaf)
-- NULL → eski kayıtlar / hat belirtilmemiş (backward compat)
ALTER TABLE public.video_jobs
  ADD COLUMN IF NOT EXISTS content_track text;

ALTER TABLE public.video_jobs
  DROP CONSTRAINT IF EXISTS video_jobs_content_track_check;

ALTER TABLE public.video_jobs
  ADD CONSTRAINT video_jobs_content_track_check
  CHECK (content_track IS NULL OR content_track IN ('ogrenci', 'danisan'));

-- ── 2. video_scenes.visual_source ────────────────────────────
-- Sahnede kullanılan görsel yüzey türü
-- text_only  → sadece metin (hook, CTA) — çeşitlilik sayımına dahil değil
-- card       → tanım kartı, hesap kartı, ipucu kutusu
-- table      → karşılaştırma tablosu
-- journal    → yevmiye kaydı
-- board      → tahta/beyaz tahta
-- photo      → gerçek fotoğraf (motivasyon sahneleri)
ALTER TABLE public.video_scenes
  ADD COLUMN IF NOT EXISTS visual_source text;

ALTER TABLE public.video_scenes
  DROP CONSTRAINT IF EXISTS video_scenes_visual_source_check;

ALTER TABLE public.video_scenes
  ADD CONSTRAINT video_scenes_visual_source_check
  CHECK (visual_source IS NULL OR visual_source IN
    ('photo', 'card', 'table', 'journal', 'board', 'text_only'));

-- ── 3. İndeksler ─────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS video_jobs_content_track
  ON public.video_jobs (content_track)
  WHERE content_track IS NOT NULL;

COMMIT;

NOTIFY pgrst, 'reload schema';

-- Doğrulama:
-- SELECT column_name, data_type FROM information_schema.columns
-- WHERE table_name IN ('video_jobs','video_scenes')
--   AND column_name IN ('content_track','visual_source')
-- ORDER BY table_name, column_name;
