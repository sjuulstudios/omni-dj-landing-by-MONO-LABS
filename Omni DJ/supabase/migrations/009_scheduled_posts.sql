-- 009_scheduled_posts.sql
-- SESSIE 71 (2026-06-02) — Content Calendar draft-store per workspace (A3).
--
-- !!! REVIEW ONLY — NOG NIET TOEGEPAST. Branch + audit eerst (zie 005). !!!
--
-- Vervangt de localStorage-drafts (sessie 56) door een echte, herinstall-bestendige
-- store. Publisht NIETS: status blijft 'draft'/'scheduled' tot de latere Postiz-fase
-- (buiten dit plan). Bevraagd via anon+user-JWT (Correctie 6). Geen postiz_post_ids
-- nog. clip_id verwijst optioneel naar public.clips (on delete set null).

create table if not exists public.scheduled_posts (
  id            uuid primary key default gen_random_uuid(),
  workspace_id  uuid not null references public.workspaces(id) on delete cascade,
  clip_id       uuid references public.clips(id) on delete set null,
  caption       text,
  platforms     text[] not null default '{}',          -- ['tiktok','instagram','youtube']
  scheduled_for timestamptz not null,
  status        text not null default 'draft' check (status in ('draft','scheduled','published','failed')),
  created_by    uuid references auth.users(id) on delete set null,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);
create index if not exists scheduled_posts_ws_when_idx on public.scheduled_posts (workspace_id, scheduled_for);

alter table public.scheduled_posts enable row level security;

drop policy if exists scheduled_posts_select on public.scheduled_posts;
create policy scheduled_posts_select on public.scheduled_posts
  for select using (public.is_workspace_member(workspace_id));

drop policy if exists scheduled_posts_insert on public.scheduled_posts;
create policy scheduled_posts_insert on public.scheduled_posts
  for insert with check (public.is_workspace_member(workspace_id));

drop policy if exists scheduled_posts_update on public.scheduled_posts;
create policy scheduled_posts_update on public.scheduled_posts
  for update using (public.is_workspace_member(workspace_id))
  with check (public.is_workspace_member(workspace_id));

drop policy if exists scheduled_posts_delete on public.scheduled_posts;
create policy scheduled_posts_delete on public.scheduled_posts
  for delete using (public.is_workspace_member(workspace_id));

-- Tabel-grants voor de authenticated-rol (anon-client + user-JWT); RLS is de grens.
grant select, insert, update, delete on public.scheduled_posts to authenticated;
