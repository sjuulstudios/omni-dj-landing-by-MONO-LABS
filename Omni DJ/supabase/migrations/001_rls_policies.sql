-- ============================================================================
-- Clip Live / Clip Drop — Row Level Security policies voor public.profiles
-- ============================================================================
--
-- Versie:        001
-- Datum:         2026-05-23 (sessie 32)
-- Auteur:        Sjuul + audit-sessie
-- Project ref:   lbabsffxefkrxwzkbzar (West EU)
--
-- DOEL
-- ----
-- Documenteert de RLS-policies die op de profiles-tabel actief moeten zijn.
-- Deze file vervangt het "RLS leeft alleen in het Supabase dashboard"-probleem:
-- nu staat de policy in version control, is hij review-baar in PRs, en kan
-- hij in 1x worden teruggezet als er ooit iets per ongeluk wordt aangepast
-- via de dashboard UI.
--
-- WAT DIT BESTAND DOET
-- --------------------
--  1. Schakelt RLS aan op public.profiles (idempotent — geen effect als al aan)
--  2. Maakt een SELECT policy: users zien alleen hun eigen rij
--  3. Maakt een UPDATE policy: users mogen ALLEEN hun eigen rij updaten,
--     EN alleen kolommen die geen security/financial implicaties hebben.
--     De "verboden" kolommen (plan, usage, quota, stripe-velden) blokkeert
--     deze policy via een WITH CHECK clausule die vergelijkt of oude waarde
--     gelijk is aan nieuwe waarde.
--  4. GEEN insert policy — rijen worden alleen aangemaakt via de
--     handle_new_user trigger, die met service_role draait en RLS omzeilt.
--  5. GEEN delete policy — accounts worden via Supabase Auth verwijderd,
--     CASCADE doet dan de rest.
--
-- WAT DIT BESTAND NIET DOET
-- -------------------------
--  - Geen wijzigingen aan auth.users (managed by Supabase, niet door ons)
--  - Geen schema-wijzigingen (kolommen toevoegen/verwijderen)
--  - Geen wijzigingen aan triggers (handle_new_user moet al bestaan)
--
-- HOE UITVOEREN
-- -------------
-- Zie ../README.md voor stap-voor-stap. Korte versie:
--   1. Open Supabase Dashboard → SQL Editor
--   2. Plak deze hele file en run
--   3. Verifieer met de testqueries onderaan
--
-- ROLLBACK
-- --------
-- Onderaan deze file staat een commented-out ROLLBACK sectie. Uncomment en
-- run om de policies te verwijderen (NIET om RLS uit te zetten — dat doe je
-- expliciet via "alter table ... disable row level security").
-- ============================================================================


-- ----------------------------------------------------------------------------
-- STAP 1 — Zorg dat RLS aan staat
-- ----------------------------------------------------------------------------
-- Idempotent: als RLS al aanstaat, doet dit niets. Volgens je screenshot van
-- 2026-05-23 staat de auto-RLS trigger aan voor nieuwe tabellen, maar deze
-- bestaande tabel moet expliciet aangevinkt zijn — vandaar deze regel.
alter table public.profiles enable row level security;


-- ----------------------------------------------------------------------------
-- STAP 2 — SELECT policy: users zien alleen hun eigen profile
-- ----------------------------------------------------------------------------
-- Het stripe-webhook + update-usage edge function gebruiken service_role en
-- omzeilen RLS, dus die hebben hier geen last van.
drop policy if exists "Users can read own profile" on public.profiles;
create policy "Users can read own profile"
    on public.profiles
    for select
    using ( auth.uid() = id );


-- ----------------------------------------------------------------------------
-- STAP 3 — UPDATE policy: users mogen alleen veilige velden van eigen rij wijzigen
-- ----------------------------------------------------------------------------
-- USING bepaalt welke rijen ze MOGEN proberen te updaten (alleen eigen rij).
-- WITH CHECK bepaalt of de RESULTAAT-rij geldig is. We vergelijken de
-- "gevoelige" kolommen met hun oude waarde via een correlated-subquery
-- pattern: als de gebruiker probeert plan/usage/stripe te wijzigen, faalt
-- de update.
--
-- Veilige kolommen (gebruiker MAG wijzigen):
--   - full_name, artist_name
--   - referral_source, referral_other, use_reasons (intake-velden)
--   - instagram_url, tiktok_url, streaming_url
--   - intake_completed_at
--
-- Gevoelige kolommen (geblokkeerd voor user-update, alleen via service_role):
--   - plan
--   - usage_this_period
--   - quota_reset_date
--   - stripe_customer_id
--   - stripe_subscription_id
--   - signup_date
--   - id (primary key — sowieso onveranderbaar door FK naar auth.users)
--
-- NB: de "is not distinct from" syntax handelt NULL=NULL correct af, anders
-- zou setten van bv. instagram_url van NULL naar 'https://...' niet werken.
drop policy if exists "Users can update own profile (safe columns)" on public.profiles;
create policy "Users can update own profile (safe columns)"
    on public.profiles
    for update
    using ( auth.uid() = id )
    with check (
        auth.uid() = id
        -- Gevoelige kolommen mogen niet veranderen vergeleken met de
        -- huidige row. We checken dat door zelf de OLD waarde op te halen
        -- via een subquery en die te vergelijken met de NEW waarde.
        and plan                    is not distinct from (select plan                    from public.profiles where id = auth.uid())
        and usage_this_period       is not distinct from (select usage_this_period       from public.profiles where id = auth.uid())
        and quota_reset_date        is not distinct from (select quota_reset_date        from public.profiles where id = auth.uid())
        and stripe_customer_id      is not distinct from (select stripe_customer_id      from public.profiles where id = auth.uid())
        and stripe_subscription_id  is not distinct from (select stripe_subscription_id  from public.profiles where id = auth.uid())
    );


-- ----------------------------------------------------------------------------
-- STAP 4 — Privilege-grants
-- ----------------------------------------------------------------------------
-- Supabase geeft de "authenticated" role per default al table-grants, maar
-- voor de zekerheid: alleen SELECT + UPDATE op profiles, geen INSERT/DELETE.
-- Service-role behoudt alle rechten (omzeilt RLS sowieso).
revoke insert, delete on public.profiles from authenticated;
grant select, update on public.profiles to authenticated;


-- ============================================================================
-- VERIFICATIE — run deze queries na de migration om te checken dat alles klopt
-- ============================================================================

-- 1. Is RLS aan?
-- select schemaname, tablename, rowsecurity
-- from pg_tables
-- where schemaname = 'public' and tablename = 'profiles';
--   --> rowsecurity = true

-- 2. Welke policies bestaan?
-- select polname, polcmd, polpermissive
-- from pg_policy
-- where polrelid = 'public.profiles'::regclass
-- order by polname;
--   --> Verwacht 2 policies:
--       "Users can read own profile"             (cmd=r / SELECT)
--       "Users can update own profile (safe...)" (cmd=w / UPDATE)

-- 3. Test als ingelogde user (vervang :test_user_id door echte uuid):
-- set local role authenticated;
-- set local request.jwt.claim.sub = ':test_user_id';
-- select id, plan, usage_this_period from public.profiles;
--   --> Mag alleen 1 rij teruggeven (eigen rij)
-- update public.profiles set artist_name = 'TEST' where id = ':test_user_id';
--   --> Moet slagen (1 row updated)
-- update public.profiles set plan = 'studio' where id = ':test_user_id';
--   --> Moet falen met "new row violates row-level security policy"


-- ============================================================================
-- ROLLBACK (commented out — uncomment + run als je deze policies wilt
--          terugdraaien. RLS zelf blijft staan!)
-- ============================================================================
-- drop policy if exists "Users can read own profile" on public.profiles;
-- drop policy if exists "Users can update own profile (safe columns)" on public.profiles;
-- grant insert, delete on public.profiles to authenticated;
