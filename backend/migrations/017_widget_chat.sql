create table if not exists public.chat_sessions (
  id uuid primary key default gen_random_uuid(),
  source text not null,
  external_id text,
  visitor_name text,
  visitor_email text,
  visitor_phone text,
  status text not null default 'active',
  bot_enabled boolean not null default true,
  created_at timestamptz not null default now(),
  last_message_at timestamptz,
  constraint chat_sessions_source_check check (source in ('website','instagram','youtube')),
  constraint chat_sessions_status_check check (status in ('active','closed','converted','manual'))
);

alter table public.chat_messages add column if not exists session_id uuid references public.chat_sessions(id);
alter table public.chat_messages alter column conversation_id drop not null;
alter table public.chat_messages alter column user_id drop not null;
create index if not exists chat_messages_session_created_idx on public.chat_messages(session_id, created_at);

grant select, insert, update on public.chat_sessions to service_role;
grant select, insert on public.chat_messages to service_role;
grant select on public.chat_sessions to authenticated;
grant select on public.chat_messages to authenticated;
alter table public.chat_sessions enable row level security;
alter table public.chat_messages enable row level security;
drop policy if exists chat_sessions_authenticated_read on public.chat_sessions;
create policy chat_sessions_authenticated_read on public.chat_sessions for select to authenticated using (true);
drop policy if exists chat_messages_authenticated_read on public.chat_messages;
create policy chat_messages_authenticated_read on public.chat_messages for select to authenticated using (true);
do $$ begin
  if not exists (select 1 from pg_publication_tables where pubname='supabase_realtime' and schemaname='public' and tablename='chat_messages') then
    alter publication supabase_realtime add table public.chat_messages;
  end if;
end $$;
select pg_notify('pgrst','reload schema');
