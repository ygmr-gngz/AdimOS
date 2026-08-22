create table if not exists public.publishing_queue (
  id uuid primary key default gen_random_uuid(),
  job_id uuid not null references public.video_jobs(id),
  platform text not null,
  content_type text not null,
  asset_urls jsonb not null,
  publish_package jsonb not null,
  scheduled_at timestamptz,
  status text not null default 'pending',
  attempt_count int not null default 0,
  last_error text,
  external_id text,
  published_at timestamptz,
  created_at timestamptz not null default now(),
  constraint publishing_queue_status_check check (status in ('pending','scheduled','publishing','published','failed','cancelled')),
  constraint publishing_queue_platform_check check (platform in ('youtube','instagram_reels','instagram_post')),
  constraint publishing_queue_content_type_check check (content_type in ('video','carousel','single_image')),
  constraint publishing_queue_job_target_unique unique(job_id, platform, content_type)
);

create index if not exists publishing_queue_due_idx
  on public.publishing_queue(status, scheduled_at, created_at);

grant select, insert, update, delete on public.publishing_queue to service_role;
select pg_notify('pgrst','reload schema');
