-- db-check.sql — son 5 işin durumunu özetler (tek sorgu).
-- Kullanım: Supabase SQL Editor'e yapıştır çalıştır, ya da:
--   psql "$DATABASE_URL" -f scripts/db-check.sql
--
-- NOT: Bu sorgu yalnızca video_jobs.storyboard (jsonb, canlıda doğrulanmış
-- kolon) üzerinden sahne istatistiklerini çıkarır — video_scenes tablosunun
-- ayrı kolonlarına (örn. captions) bağımlı DEĞİLDİR, çünkü o kolonun canlıda
-- var olduğu doğrulanamadı (bkz. final rapor "kalan riskler" — 014
-- migration'ının canlıya hiç uygulanmadığı zaten biliniyor). storyboard,
-- Remotion'a gönderilen gerçek veridir; video_scenes'ten daha güvenilir kaynak.
--
-- render_cost_usd kolonu KULLANILMIYOR — canlıda yok (postmortem, bkz. final
-- rapor M1/M6). Gerçek maliyet kolonları: cost_lambda_usd, cost_llm_usd,
-- cost_tts_usd, cost_total_usd_est, image_cost_usd.

select
  vj.id,
  vj.type,
  vj.status,
  vj.error_code,
  vj.created_at,

  -- Render-sonrası süre kapalı döngüsü (bkz. render_callback / admin_detail)
  (vj.admin_detail ->> 'duration_postrender_turn')::int as postrender_turn,
  vj.admin_detail -> 'budget_exceeded'                  as budget_exceeded,
  (vj.admin_detail ->> 'cost_tracking_broken')::boolean as cost_tracking_broken,

  -- Sahne istatistikleri — storyboard jsonb'den (tek kaynak, video_scenes'e bağımlı değil)
  jsonb_array_length(coalesce(vj.storyboard -> 'scenes', '[]'::jsonb)) as scene_count,
  (
    select sum((s ->> 'duration_seconds')::numeric)
    from jsonb_array_elements(coalesce(vj.storyboard -> 'scenes', '[]'::jsonb)) as s
  ) as scene_duration_sum,
  (
    select jsonb_object_agg(ds, cnt)
    from (
      select coalesce(s ->> 'duration_source', 'null') as ds, count(*) as cnt
      from jsonb_array_elements(coalesce(vj.storyboard -> 'scenes', '[]'::jsonb)) as s
      group by 1
    ) t
  ) as duration_source_dist,
  (
    select count(*)
    from jsonb_array_elements(coalesce(vj.storyboard -> 'scenes', '[]'::jsonb)) as s
    where jsonb_array_length(coalesce(s -> 'captions', '[]'::jsonb)) > 0
  ) as scenes_with_captions,

  -- Süre kalite kapısı
  vj.requested_duration_seconds,
  vj.duration_tolerance_seconds,
  vj.actual_duration_seconds,

  -- Postcheck (render sonrası ölçüm)
  (vj.postcheck_report -> 'duration_check' ->> 'ok')::boolean    as postcheck_duration_ok,
  (vj.postcheck_report ->> 'integrated_lufs')::numeric            as integrated_lufs,
  (vj.postcheck_report ->> 'audio_volume_db')::numeric            as audio_volume_db,
  vj.postcheck_report ->> 'first_failure_code'                    as postcheck_first_failure_code,

  -- Maliyet — canlı kolon adları (render_cost_usd YOK)
  vj.cost_lambda_usd,
  vj.cost_llm_usd,
  vj.cost_tts_usd,
  vj.cost_total_usd_est,
  vj.image_cost_usd

from video_jobs vj
order by vj.created_at desc
limit 5;
