-- 005_workspaces.sql
-- SESSIE 71 (2026-06-02) — A1 multi-tenant fundament (Spoor A van PLAN-COMBINED v1.3).
--
-- !!! REVIEW ONLY — NOG NIET TOEGEPAST OP HET LIVE PROJECT. !!!
-- Toepassen EERST op een Supabase-branch (mcp create_branch), dan de audit-harness
-- (audit/AUDIT_cross_account_rls.sql) groen draaien, PAS DAARNA mergen naar main.
--
-- KERN-ARCHITECTUUR (PLAN v1.3, Correctie 6): de Flask-backend draait vandaag alle
-- queries via de service_role-key (supabase_admin) en OMZEILT RLS volledig. Deze
-- nieuwe content-tabellen MOETEN daarom door de backend bevraagd worden via de
-- ANON-client gebonden aan de USER-JWT (postgrest.auth(jwt)), zodat auth.uid()
-- klopt en RLS de echte isolatie-grens is. supabase_admin blijft alleen voor
-- profiel/role/billing. Zonder dit is RLS nutteloos en lekt data tussen artists.
--
-- Bevat: workspaces + workspace_members + membership-helpers (SECURITY DEFINER,
-- search_path locked, conform sessie 67) + owner-as-member trigger +
-- profiles.max_workspaces + idempotente backfill van 1 default-workspace per profiel.
-- RLS-policies staan in 006 (apart, want hoogste-risico-stap).

-- ---------------------------------------------------------------------------
-- 1) Tabellen
-- ---------------------------------------------------------------------------
create table if not exists public.workspaces (
  id          uuid primary key default gen_random_uuid(),
  name        text not null,
  slug        text unique,
  owner_id    uuid not null references auth.users(id) on delete cascade,
  artist_name text,
  avatar_url  text,
  settings    jsonb not null default '{}'::jsonb,   -- C8: panel-layout / editor- + export-defaults per workspace
  created_at  timestamptz not null default now()
);
create index if not exists workspaces_owner_idx on public.workspaces (owner_id);

create table if not exists public.workspace_members (
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  user_id      uuid not null references auth.users(id) on delete cascade,
  role         text not null check (role in ('owner','editor','viewer')) default 'editor',
  invited_at   timestamptz not null default now(),
  primary key (workspace_id, user_id)
);
create index if not exists workspace_members_user_idx on public.workspace_members (user_id);

-- Plan-afgeleide limiet, INSTELBAAR zonder migratie (beslissing 3 sessie 70).
-- FREE/Solo praktisch 1; Studio-getal (3 of 5) wordt later beslist en in
-- billing.py op deze kolom gezet. Default 1 is veilig.
alter table public.profiles add column if not exists max_workspaces integer not null default 1;

-- ---------------------------------------------------------------------------
-- 2) Membership-helpers — SECURITY DEFINER zodat RLS-policies GEEN recursie
--    krijgen (een policy op workspace_members die workspace_members zou
--    bevragen recurset; via een definer-functie wordt RLS omzeild in de check).
--    search_path locked (sessie 67-patroon). EXECUTE alleen voor authenticated.
-- ---------------------------------------------------------------------------
create or replace function public.is_workspace_member(p_workspace uuid)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1 from public.workspace_members m
    where m.workspace_id = p_workspace
      and m.user_id = auth.uid()
  );
$$;

create or replace function public.is_workspace_owner(p_workspace uuid)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1 from public.workspaces w
    where w.id = p_workspace
      and w.owner_id = auth.uid()
  );
$$;

revoke all on function public.is_workspace_member(uuid) from public, anon;
revoke all on function public.is_workspace_owner(uuid)  from public, anon;
grant execute on function public.is_workspace_member(uuid) to authenticated;
grant execute on function public.is_workspace_owner(uuid)  to authenticated;

-- Tabel-grants (sessie 71, geverifieerd nodig via branch-audit): de backend bevraagt
-- deze tabellen als rol 'authenticated' (anon-client + user-JWT), dus authenticated
-- heeft tabel-rechten nodig; RLS is daarbinnen de grens. service_role omzeilt RLS en
-- heeft al toegang; anon krijgt NIETS op deze tabellen.
grant usage on schema public to authenticated;
grant select, insert, update, delete on public.workspaces, public.workspace_members to authenticated;

-- ---------------------------------------------------------------------------
-- 3) Trigger: voeg de owner automatisch toe als 'owner'-member bij aanmaak.
--    Zo hoeft de app geen tweede insert te doen en is de bootstrap RLS-veilig.
-- ---------------------------------------------------------------------------
create or replace function public.add_owner_as_member()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.workspace_members (workspace_id, user_id, role)
  values (new.id, new.owner_id, 'owner')
  on conflict (workspace_id, user_id) do nothing;
  return new;
end;
$$;

drop trigger if exists trg_add_owner_as_member on public.workspaces;
create trigger trg_add_owner_as_member
  after insert on public.workspaces
  for each row execute function public.add_owner_as_member();

-- Trigger-functie hoort NIET RPC-callable te zijn (sessie 67-patroon). De trigger
-- blijft werken (draait als functie-owner); alleen de directe /rest/v1/rpc-route weg.
revoke execute on function public.add_owner_as_member() from public, anon, authenticated;

-- ---------------------------------------------------------------------------
-- 4) Data-migratie (idempotent): 1 default-workspace per bestaand profiel.
--    Draait als migratie-rol (RLS niet van toepassing). Alleen aanmaken als de
--    user nog NERGENS member is. De trigger zet de owner-membership erbij.
-- ---------------------------------------------------------------------------
do $$
declare r record;
begin
  for r in
    select p.id as uid,
           coalesce(nullif(trim(p.artist_name), ''),
                    nullif(trim(p.full_name), ''),
                    'My workspace') as nm
    from public.profiles p
  loop
    if not exists (select 1 from public.workspace_members m where m.user_id = r.uid) then
      insert into public.workspaces (name, owner_id, artist_name)
      values (r.nm, r.uid, r.nm);
    end if;
  end loop;
end $$;
