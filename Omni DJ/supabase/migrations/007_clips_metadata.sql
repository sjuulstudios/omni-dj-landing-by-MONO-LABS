-- 007_clips_metadata.sql
-- SESSIE 71 (2026-06-02) — lichte clip-metadata per workspace (A1).
--
-- !!! REVIEW ONLY — NOG NIET TOEGEPAST. Branch + audit eerst (zie 005). !!!
--
-- GEEN media in de cloud: alleen een lichte verwijzing (local_path) + labels zodat
-- de Calendar (A3) een clip per workspace kan kiezen. De echte video/audio blijft
-- lokaal onder workspaces/<id>/ (DATA_DIR). Bevraagd via anon+user-JWT (Correctie 6).

create table if not exists public.clips (
  id           uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  local_path   text,                       -- verwijzing naar het bestand op de machine
  label        text,
  duration_s   numeric,
  source_set   text,                       -- bron-set / job-id-naam (lokaal)
  kind         text default 'clip' check (kind in ('clip','import','sync')),
  created_at   timestamptz not null default now()
);
create index if not exists clips_workspace_created_idx on public.clips (workspace_id, created_at desc);

alter table public.clips enable row level security;

drop policy if exists clips_select on public.clips;
create policy clips_select on public.clips
  for select using (public.is_workspace_member(workspace_id));

drop policy if exists clips_insert on public.clips;
create policy clips_insert on public.clips
  for insert with check (public.is_workspace_member(workspace_id));

drop policy if exists clips_update on public.clips;
create policy clips_update on public.clips
  for update using (public.is_workspace_member(workspace_id))
  with check (public.is_workspace_member(workspace_id));

drop policy if exists clips_delete on public.clips;
create policy clips_delete on public.clips
  for delete using (public.is_workspace_member(workspace_id));

-- Tabel-grants voor de authenticated-rol (anon-client + user-JWT); RLS is de grens.
grant select, insert, update, delete on public.clips to authenticated;
