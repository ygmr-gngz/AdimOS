-- AdimOS Migration 015 — Görsel kütüphane (motivasyon foto arka planları)
-- Supabase SQL Editor'da çalıştır.
--
-- Neden DB, neden Storage (repo-root assets/ değil):
--   1. Railway'de backend'in Docker build context'i backend/ (Root Directory) —
--      repo kökündeki assets/ imajda yok; runtime'da local dosya okumaya
--      çalışmak import-time/request-time crash'e yol açar (content_constants.py
--      postmortem ile aynı hata sınıfı).
--   2. Render işlemi AWS Lambda üzerinde (Remotion) çalışır — backend'in
--      local diskine hiçbir şekilde erişemez. Görsellerin gerçek bir HTTP
--      URL'i olması ZORUNLU (Supabase Storage public URL), local dosya yolu
--      değil.
--
-- Çalıştırma sonrası doğrulama:
--   SELECT column_name, data_type FROM information_schema.columns
--   WHERE table_name = 'visual_assets' ORDER BY ordinal_position;

BEGIN;

CREATE TABLE IF NOT EXISTS public.visual_assets (
  id                     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  asset_id               text NOT NULL,
  theme                  text NOT NULL,
  cache_key              text NOT NULL,
  source                 text NOT NULL DEFAULT 'openai_image_api',
  model                  text NOT NULL,
  quality                text NOT NULL,
  storage_path           text NOT NULL,
  public_url             text NOT NULL,
  sha256                 text NOT NULL,
  width                  integer,
  height                 integer,
  license                text,
  license_url            text,
  attribution_required   boolean NOT NULL DEFAULT false,
  ocr_clean              boolean NOT NULL DEFAULT false,
  ocr_text               text,
  blur_variance          numeric,
  brightness_avg         numeric,
  upper_third_flatness   numeric,
  has_face               boolean NOT NULL DEFAULT false,
  tags                   jsonb NOT NULL DEFAULT '[]'::jsonb,
  dominant_color         text,
  generated_at           timestamptz NOT NULL DEFAULT now(),
  created_at             timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE public.visual_assets
  ADD CONSTRAINT visual_assets_asset_id_unique UNIQUE (asset_id);
ALTER TABLE public.visual_assets
  ADD CONSTRAINT visual_assets_cache_key_unique UNIQUE (cache_key);

-- Seçim algoritması tema + lisans filtreli sorgu yapar — bileşik indeks
CREATE INDEX IF NOT EXISTS visual_assets_theme_license
  ON public.visual_assets (theme, license);

-- Boş/NULL license render'a giremez (asset_license_missing) — bu bir uygulama
-- seviyesi kapı, ama DB'de de görünür olması için CHECK eklemiyoruz (kayıt
-- her zaman izinli olmayabilir, önce üretilip sonra lisans doğrulanabilir);
-- filtre visual_library.py'de `license IS NOT NULL AND license <> ''` ile yapılır.

-- video_scenes.image_asset_id zaten mevcut (014 migration) — visual_assets.asset_id'yi referans eder (soft FK, cross-service)

COMMIT;

NOTIFY pgrst, 'reload schema';

-- ── Doğrulama sorguları ──────────────────────────────────────────
-- SELECT column_name, data_type FROM information_schema.columns
-- WHERE table_name = 'visual_assets' ORDER BY ordinal_position;
--
-- SELECT theme, count(*) FILTER (WHERE license IS NOT NULL AND license <> '') AS licensed,
--        count(*) AS total
-- FROM visual_assets GROUP BY theme ORDER BY theme;
