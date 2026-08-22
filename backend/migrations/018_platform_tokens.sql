create table if not exists public.platform_tokens (
  platform text primary key,
  refresh_token text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.platform_tokens enable row level security;

revoke all on public.platform_tokens from anon, authenticated;
grant select, insert, update, delete on public.platform_tokens to service_role;

select pg_notify('pgrst', 'reload schema');
