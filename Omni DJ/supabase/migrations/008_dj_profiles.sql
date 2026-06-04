-- 008_dj_profiles.sql
-- SESSIE 71 (2026-06-02) — Brand-architectuur per workspace (A2).
--
-- !!! REVIEW ONLY — NOG NIET TOEGEPAST. Branch + audit eerst (zie 005). !!!
--
-- 1 brand-profiel per workspace + N templates per profiel. Het `profile` jsonb
-- volgt het schema uit PLAN-MOAT-FEATURES §3 (artist_name, alias, visual,
-- typography, lower_third, cta met Spotify/Beatport, hashtags per platform,
-- caption_voice). Assets (logo/fonts/watermark) gaan naar Supabase Storage in een
-- per-workspace pad + lokale cache; dit dekt alleen de metadata. Bevraagd via
-- anon+user-JWT (Correctie 6). dj_templates wordt member-gescoped via het profiel
-- (join naar de workspace van het profiel).

create table if not exists public.dj_profiles (
  id           uuid primary key default gen_random_uuid(),
  workspace_id uuid unique not null references public.workspaces(id) on delete cascade,
  profile      jsonb not null default '{}'::jsonb,
  updated_at   timestamptz not null default now()
);

create table if not exists public.dj_templates (
  id           uuid primary key default gen_random_uuid(),
  profile_id   uuid not null references public.dj_profiles(id) on delete cascade,
  name         text not null,             -- "Festival-clip" / "Studio-mix" / "Track-release"
  overrides    jsonb not null default '{}'::jsonb,
  created_at   timestamptz not null default now()
);
create index if not exists dj_templates_profile_idx on public.dj_templates (profile_id);

-- Helper: is de huidige user member van de workspace die bij dit profiel hoort?
-- SECURITY DEFINER zodat de policy op dj_templates niet via RLS hoeft te joinen.
create or replace function public.can_access_dj_profile(p_profile uuid)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1
    from public.dj_profiles pr
    join public.workspace_members m on m.workspace_id = pr.workspace_id
    where pr.id = p_profile
      and m.user_id = auth.uid()
  );
$$;
revoke all on function public.can_access_dj_profile(uuid) from public, anon;
grant execute on function public.can_access_dj_profile(uuid) to authenticated;

-- ---- dj_profiles RLS ----
alter table public.dj_profiles enable row level security;

drop policy if exists dj_profiles_select on public.dj_profiles;
create policy dj_profiles_select on public.dj_profiles
  for select using (public.is_workspace_member(workspace_id));

drop policy if exists dj_profiles_insert on public.dj_profiles;
create policy dj_profiles_insert on public.dj_profiles
  for insert with check (public.is_workspace_member(workspace_id));

drop policy if exists dj_profiles_update on public.dj_profiles;
create policy dj_profiles_update on public.dj_profiles
  for update using (public.is_workspace_member(workspace_id))
  with check (public.is_workspace_member(workspace_id));

drop policy if exists dj_profiles_delete on public.dj_profiles;
create policy dj_profiles_delete on public.dj_profiles
  for delete using (public.is_workspace_owner(workspace_id));

-- ---- dj_templates RLS (via het profiel) ----
alter table public.dj_templates enable row level security;

drop policy if exists dj_templates_select on public.dj_templates;
create policy dj_templates_select on public.dj_templates
  for select using (public.can_access_dj_profile(profile_id));

drop policy if exists dj_templates_insert on public.dj_templates;
create policy dj_templates_insert on public.dj_templates
  for insert with check (public.can_access_dj_profile(profile_id));

drop policy if exists dj_templates_update on public.dj_templates;
create policy dj_templates_update on public.dj_templates
  for update using (public.can_access_dj_profile(profile_id))
  with check (public.can_access_dj_profile(profile_id));

drop policy if exists dj_templates_delete on public.dj_templates;
create policy dj_templates_delete on public.dj_templates
  for delete using (public.can_access_dj_profile(profile_id));

-- Tabel-grants voor de authenticated-rol (anon-client + user-JWT); RLS is de grens.
grant select, insert, update, delete on public.dj_profiles, public.dj_templates to authenticated;
