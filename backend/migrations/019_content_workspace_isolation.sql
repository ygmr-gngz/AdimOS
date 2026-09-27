-- Content RAG workspace isolation. Backward compatible for the existing
-- single-workspace deployment: all historical rows are assigned to "default".
alter table public.documents
  add column if not exists workspace_id text not null default 'default';

alter table public.chunks
  add column if not exists workspace_id text not null default 'default';

update public.chunks c
set workspace_id = d.workspace_id
from public.documents d
where c.document_id = d.id
  and c.workspace_id is distinct from d.workspace_id;

create index if not exists documents_workspace_id_idx
  on public.documents (workspace_id);
create index if not exists chunks_workspace_id_idx
  on public.chunks (workspace_id);

create or replace function public.match_chunks_scoped(
  query_embedding vector,
  match_count integer,
  match_threshold double precision,
  filter_workspace_id text
)
returns table (
  id uuid,
  document_id uuid,
  chunk_data text,
  similarity double precision
)
language sql
stable
security invoker
set search_path = public
as $$
  select
    c.id,
    c.document_id,
    c.chunk_data,
    1 - (c.embedding <=> query_embedding) as similarity
  from public.chunks c
  where c.workspace_id = filter_workspace_id
    and 1 - (c.embedding <=> query_embedding) >= match_threshold
  order by c.embedding <=> query_embedding
  limit least(match_count, 50);
$$;

revoke all on function public.match_chunks_scoped(vector, integer, double precision, text)
  from public, anon, authenticated;
grant execute on function public.match_chunks_scoped(vector, integer, double precision, text)
  to service_role;

-- Make the new RPC visible immediately to PostgREST after SQL Editor/migration runs.
notify pgrst, 'reload schema';
