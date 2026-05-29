-- ============================================================================
-- Clip Live / Clip Drop — RBAC: role kolom op profiles
-- ============================================================================
--
-- Versie:        003
-- Datum:         2026-05-24 (sessie 35)
-- Auteur:        Sjuul + Claude (autonoom)
-- Project ref:   lbabsffxefkrxwzkbzar (West EU)
--
-- DOEL
-- ----
-- Voegt een `role` kolom toe aan public.profiles zodat de app onderscheid
-- kan maken tussen gewone gebruikers, beta-testers, en admins (Sjuul zelf).
-- Dit is de basis voor:
--  - Admin-endpoints afsluiten voor gewone users (bv. /api/debug/logs, toekomstig /api/admin/*)
--  - Beta-toegang beperken tot uitgenodigde testers
--  - Toekomstige team-accounts met per-rol rechten
--
-- Beschikbare rollen:
--   user  — standaard voor alle nieuwe accounts (default)
--   beta  — beta-testers die extra features zien
--   admin — volledige toegang, inclusief admin-endpoints
--
-- WAT DIT BESTAND DOET
-- --------------------
--  1. Voegt `role` kolom toe (text, default 'user', not null)
--  2. Voegt een check constraint toe zodat alleen geldige waarden worden opgeslagen
--  3. Updatet de bestaande UPDATE RLS-policy zodat users hun eigen role
--     NIET kunnen verhogen (alleen service_role mag dat)
--  4. Maakt Sjuul zelf admin (via service_role, zie instructies onderaan)
--
-- WAT DIT BESTAND NIET DOET
-- -------------------------
--  - Geen nieuwe tabellen, geen triggers
--  - De `require_role` decorator in Python is een aparte code-change (auth.py)
--
-- HOE UITVOEREN
-- -------------
--  1. Open Supabase Dashboard → SQL Editor
--  2. Plak deze hele file en run
--  3. Verifieer met de testqueries onderaan
--  4. Maak jezelf admin: zie STAP 4 onderaan
--
-- ROLLBACK
-- --------
-- Zie onderaan dit bestand.
-- ============================================================================


-- ----------------------------------------------------------------------------
-- STAP 1 — role kolom toevoegen
-- ----------------------------------------------------------------------------
-- Idempotent: als de kolom al bestaat, doet alter table ... add column if not exists niets.
alter table public.profiles
    add column if not exists role text not null default 'user';

-- Check constraint: alleen geldige waarden
-- (drop first zodat re-run idempotent is)
alter table public.profiles
    drop constraint if exists profiles_role_check;
alter table public.profiles
    add constraint profiles_role_check
    check (role in ('user', 'beta', 'admin'));


-- ----------------------------------------------------------------------------
-- STAP 2 — UPDATE RLS-policy uitbreiden: role mag niet via user zelf worden verhoogd
-- ----------------------------------------------------------------------------
-- De bestaande policy (001_rls_policies.sql) blokkeert al plan/usage/stripe.
-- We voegen `role` toe aan die lijst.
drop policy if exists "Users can update own profile (safe columns)" on public.profiles;
create policy "Users can update own profile (safe columns)"
    on public.profiles
    for update
    using ( auth.uid() = id )
    with check (
        auth.uid() = id
        and plan                    is not distinct from (select plan                    from public.profiles where id = auth.uid())
        and usage_this_period       is not distinct from (select usage_this_period       from public.profiles where id = auth.uid())
        and quota_reset_date        is not distinct from (select quota_reset_date        from public.profiles where id = auth.uid())
        and stripe_customer_id      is not distinct from (select stripe_customer_id      from public.profiles where id = auth.uid())
        and stripe_subscription_id  is not distinct from (select stripe_subscription_id  from public.profiles where id = auth.uid())
        and role                    is not distinct from (select role                    from public.profiles where id = auth.uid())
    );


-- ============================================================================
-- STAP 3 — Sjuul's account admin maken
-- ============================================================================
-- Vervang het email-adres door jouw echte email, en run dit APART in de
-- SQL Editor nadat stap 1+2 succesvol zijn:
--
-- update public.profiles
-- set role = 'admin'
-- where id = (
--     select id from auth.users where email = 'business@sjuulstudios.com'
-- );
--
-- Verifieer: select id, role from public.profiles
--            where id = (select id from auth.users where email = 'business@sjuulstudios.com');
-- --> role = admin


-- ============================================================================
-- VERIFICATIE — run na de migration
-- ============================================================================

-- 1. Kolom aanwezig met default?
-- select column_name, data_type, column_default
-- from information_schema.columns
-- where table_schema = 'public' and table_name = 'profiles' and column_name = 'role';
--   --> role | text | 'user'::text

-- 2. Check constraint aanwezig?
-- select constraint_name, check_clause
-- from information_schema.check_constraints
-- where constraint_name = 'profiles_role_check';
--   --> profiles_role_check | (role = ANY (ARRAY['user'::text, 'beta'::text, 'admin'::text]))

-- 3. Bestaande users hebben role='user'?
-- select count(*) from public.profiles where role = 'user';
--   --> alle bestaande gebruikers

-- 4. Test dat user role niet zelf kan verhogen (vervang :uid):
-- set local role authenticated;
-- set local request.jwt.claim.sub = ':uid';
-- update public.profiles set role = 'admin' where id = ':uid';
--   --> Moet falen: "new row violates row-level security policy"


-- ============================================================================
-- ROLLBACK (commented out)
-- ============================================================================
-- alter table public.profiles drop constraint if exists profiles_role_check;
-- alter table public.profiles drop column if exists role;
-- -- Herstel de originele UPDATE policy zonder role-check (kopieer uit 001_rls_policies.sql)
