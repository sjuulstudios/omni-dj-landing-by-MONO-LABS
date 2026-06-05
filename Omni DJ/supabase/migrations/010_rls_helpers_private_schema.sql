-- 010_rls_helpers_private_schema.sql
-- SESSIE 71 (2026-06-02) — OPTIONELE hardening. Verplaatst de RLS-helper-functies
-- naar een niet-via-PostgREST-geexposeerd schema `private`, zodat ze niet meer
-- als /rest/v1/rpc aanroepbaar zijn. Lost de 3 resterende advisor-WARNs op
-- (is_workspace_member / is_workspace_owner / can_access_dj_profile).
--
-- APPLIED op main 2026-06-04 (sessie 76) na groene branch-audit. Zie HANDOVER sessie 76.
--
-- Achtergrond: deze helpers MOETEN door 'authenticated' uitvoerbaar zijn (RLS
-- evalueert ze), dus revoke (sessie 67-patroon) kan NIET. Ze lekken zelf geen
-- data van anderen (alle checks zijn auth.uid()-gebaseerd = alleen de caller),
-- dus de WARN is laag-risico. Deze migratie is netjes-maar-niet-urgent.
--
-- LET OP: policies binden aan de functie; verplaatsen vereist policies opnieuw
-- aanmaken. Daarom hier alles in 1 migratie. Na toepassen: her-run de
-- cross-account audit (AUDIT_cross_account_rls.sql) want RLS is geraakt.

create schema if not exists private;

-- 1) Helpers opnieuw in `private` (zelfde body, search_path = public zodat ze de
--    publieke tabellen blijven zien).
create or replace function private.is_workspace_member(p_workspace uuid)
returns boolean language sql stable security definer set search_path = public as $$
  select exists (select 1 from public.workspace_members m
                 where m.workspace_id = p_workspace and m.user_id = auth.uid());
$$;

create or replace function private.is_workspace_owner(p_workspace uuid)
returns boolean language sql stable security definer set search_path = public as $$
  select exists (select 1 from public.workspaces w
                 where w.id = p_workspace and w.owner_id = auth.uid());
$$;

create or replace function private.can_access_dj_profile(p_profile uuid)
returns boolean language sql stable security definer set search_path = public as $$
  select exists (
    select 1 from public.dj_profiles pr
    join public.workspace_members m on m.workspace_id = pr.workspace_id
    where pr.id = p_profile and m.user_id = auth.uid()
  );
$$;

-- `private` is niet in de PostgREST-exposed schemas, dus deze functies zijn niet
-- via /rest/v1/rpc aanroepbaar. authenticated heeft wel EXECUTE nodig voor RLS.
revoke all on function private.is_workspace_member(uuid)  from public, anon;
revoke all on function private.is_workspace_owner(uuid)   from public, anon;
revoke all on function private.can_access_dj_profile(uuid) from public, anon;
grant usage on schema private to authenticated;
grant execute on function private.is_workspace_member(uuid)  to authenticated;
grant execute on function private.is_workspace_owner(uuid)   to authenticated;
grant execute on function private.can_access_dj_profile(uuid) to authenticated;

-- 2) Policies opnieuw aanmaken zodat ze naar private.* verwijzen.
-- workspaces
drop policy if exists workspaces_select on public.workspaces;
create policy workspaces_select on public.workspaces for select using (owner_id = auth.uid() or private.is_workspace_member(id));
drop policy if exists workspaces_update on public.workspaces;
create policy workspaces_update on public.workspaces for update using (private.is_workspace_owner(id)) with check (private.is_workspace_owner(id));
drop policy if exists workspaces_delete on public.workspaces;
create policy workspaces_delete on public.workspaces for delete using (private.is_workspace_owner(id));
-- workspace_members
drop policy if exists members_select on public.workspace_members;
create policy members_select on public.workspace_members for select using (private.is_workspace_member(workspace_id));
drop policy if exists members_insert on public.workspace_members;
create policy members_insert on public.workspace_members for insert with check (private.is_workspace_owner(workspace_id));
drop policy if exists members_update on public.workspace_members;
create policy members_update on public.workspace_members for update using (private.is_workspace_owner(workspace_id)) with check (private.is_workspace_owner(workspace_id));
drop policy if exists members_delete on public.workspace_members;
create policy members_delete on public.workspace_members for delete using (private.is_workspace_owner(workspace_id) or user_id = auth.uid());
-- clips
drop policy if exists clips_select on public.clips;
create policy clips_select on public.clips for select using (private.is_workspace_member(workspace_id));
drop policy if exists clips_insert on public.clips;
create policy clips_insert on public.clips for insert with check (private.is_workspace_member(workspace_id));
drop policy if exists clips_update on public.clips;
create policy clips_update on public.clips for update using (private.is_workspace_member(workspace_id)) with check (private.is_workspace_member(workspace_id));
drop policy if exists clips_delete on public.clips;
create policy clips_delete on public.clips for delete using (private.is_workspace_member(workspace_id));
-- dj_profiles
drop policy if exists dj_profiles_select on public.dj_profiles;
create policy dj_profiles_select on public.dj_profiles for select using (private.is_workspace_member(workspace_id));
drop policy if exists dj_profiles_insert on public.dj_profiles;
create policy dj_profiles_insert on public.dj_profiles for insert with check (private.is_workspace_member(workspace_id));
drop policy if exists dj_profiles_update on public.dj_profiles;
create policy dj_profiles_update on public.dj_profiles for update using (private.is_workspace_member(workspace_id)) with check (private.is_workspace_member(workspace_id));
drop policy if exists dj_profiles_delete on public.dj_profiles;
create policy dj_profiles_delete on public.dj_profiles for delete using (private.is_workspace_owner(workspace_id));
-- dj_templates
drop policy if exists dj_templates_select on public.dj_templates;
create policy dj_templates_select on public.dj_templates for select using (private.can_access_dj_profile(profile_id));
drop policy if exists dj_templates_insert on public.dj_templates;
create policy dj_templates_insert on public.dj_templates for insert with check (private.can_access_dj_profile(profile_id));
drop policy if exists dj_templates_update on public.dj_templates;
create policy dj_templates_update on public.dj_templates for update using (private.can_access_dj_profile(profile_id)) with check (private.can_access_dj_profile(profile_id));
drop policy if exists dj_templates_delete on public.dj_templates;
create policy dj_templates_delete on public.dj_templates for delete using (private.can_access_dj_profile(profile_id));
-- scheduled_posts
drop policy if exists scheduled_posts_select on public.scheduled_posts;
create policy scheduled_posts_select on public.scheduled_posts for select using (private.is_workspace_member(workspace_id));
drop policy if exists scheduled_posts_insert on public.scheduled_posts;
create policy scheduled_posts_insert on public.scheduled_posts for insert with check (private.is_workspace_member(workspace_id));
drop policy if exists scheduled_posts_update on public.scheduled_posts;
create policy scheduled_posts_update on public.scheduled_posts for update using (private.is_workspace_member(workspace_id)) with check (private.is_workspace_member(workspace_id));
drop policy if exists scheduled_posts_delete on public.scheduled_posts;
create policy scheduled_posts_delete on public.scheduled_posts for delete using (private.is_workspace_member(workspace_id));

-- 3) Oude public-helpers weg (geen policy verwijst er meer naar).
drop function if exists public.is_workspace_member(uuid);
drop function if exists public.is_workspace_owner(uuid);
drop function if exists public.can_access_dj_profile(uuid);