-- ============================================================================
-- Clip Live / Clip Drop — Audit log tabel + RLS
-- ============================================================================
--
-- Versie:        002
-- Datum:         2026-05-24 (sessie 35)
-- Auteur:        Sjuul + Claude (autonoom)
-- Project ref:   lbabsffxefkrxwzkbzar (West EU)
--
-- DOEL
-- ----
-- Registreert elke significante actie in de app: wie deed wat, wanneer,
-- vanaf welk IP-adres. Dit is:
--  - Een SOC 2 / enterprise vereiste ("show me your audit log")
--  - Nuttig voor support en debugging
--  - De basis voor toekomstige compliance-rapportages
--
-- WAT DIT BESTAND DOET
-- --------------------
--  1. Maakt de tabel public.audit_logs aan (idempotent via CREATE IF NOT EXISTS)
--  2. Maakt een index op user_id + created_at voor snelle queries
--  3. Schakelt RLS in
--  4. SELECT policy: users zien alleen hun eigen logs
--  5. INSERT policy: alleen service_role mag schrijven (via log_action() helper)
--     — gewone users mogen NOOIT zelf audit_logs aanmaken of aanpassen
--  6. Geen UPDATE/DELETE policy — audit logs zijn immutable by design
--
-- WAT DIT BESTAND NIET DOET
-- -------------------------
--  - Geen wijzigingen aan profiles of auth.users
--  - Geen triggers — logging gebeurt expliciet vanuit Python (log_action())
--
-- HOE UITVOEREN
-- -------------
--  1. Open Supabase Dashboard → SQL Editor
--  2. Plak deze hele file en run
--  3. Verifieer met de testqueries onderaan
--
-- ROLLBACK
-- --------
-- Zie onderaan dit bestand.
-- ============================================================================


-- ----------------------------------------------------------------------------
-- STAP 1 — Tabel aanmaken
-- ----------------------------------------------------------------------------
create table if not exists public.audit_logs (
    id              uuid primary key default gen_random_uuid(),
    user_id         uuid references auth.users(id) on delete set null,
    action          text not null,
    ip_address      text,
    user_agent      text,
    metadata        jsonb default '{}'::jsonb,
    created_at      timestamptz not null default now()
);

-- Commentaar op kolommen voor documentatie in Supabase Dashboard
comment on table  public.audit_logs             is 'Immutable audit trail van alle significante acties. Nooit handmatig aanpassen.';
comment on column public.audit_logs.user_id     is 'NULL als actie plaatsvond vóór login (bv. mislukte login-poging).';
comment on column public.audit_logs.action      is 'Vaste action-string, bv. "auth.login", "clip.export", "plan.upgrade".';
comment on column public.audit_logs.ip_address  is 'IPv4 of IPv6 adres van de client op moment van de actie.';
comment on column public.audit_logs.user_agent  is 'Browser/app user-agent string.';
comment on column public.audit_logs.metadata    is 'Extra context afhankelijk van de action, bv. {"plan":"studio","clip_id":"..."}.';


-- ----------------------------------------------------------------------------
-- STAP 2 — Index voor snelle queries op user + tijd
-- ----------------------------------------------------------------------------
create index if not exists audit_logs_user_id_created_at_idx
    on public.audit_logs (user_id, created_at desc);

-- Extra index voor action-type zoekopdrachten (handig voor rapportages)
create index if not exists audit_logs_action_created_at_idx
    on public.audit_logs (action, created_at desc);


-- ----------------------------------------------------------------------------
-- STAP 3 — RLS aanzetten
-- ----------------------------------------------------------------------------
alter table public.audit_logs enable row level security;


-- ----------------------------------------------------------------------------
-- STAP 4 — SELECT policy: users zien alleen hun eigen logs
-- ----------------------------------------------------------------------------
drop policy if exists "Users can read own audit logs" on public.audit_logs;
create policy "Users can read own audit logs"
    on public.audit_logs
    for select
    using ( auth.uid() = user_id );


-- ----------------------------------------------------------------------------
-- STAP 5 — Privilege-grants
-- ----------------------------------------------------------------------------
-- Authenticated users mogen ALLEEN SELECT op eigen rijen (via policy hierboven).
-- INSERT/UPDATE/DELETE alleen via service_role (de Python backend).
-- Dit voorkomt dat een user zelf fake audit-entries kan aanmaken.
revoke insert, update, delete on public.audit_logs from authenticated;
grant select on public.audit_logs to authenticated;


-- ============================================================================
-- VERIFICATIE — run na de migration
-- ============================================================================

-- 1. Tabel aanwezig?
-- select table_name from information_schema.tables
-- where table_schema = 'public' and table_name = 'audit_logs';
--   --> 1 rij: audit_logs

-- 2. RLS aan?
-- select schemaname, tablename, rowsecurity
-- from pg_tables
-- where schemaname = 'public' and tablename = 'audit_logs';
--   --> rowsecurity = true

-- 3. Policies aanwezig?
-- select polname, polcmd from pg_policy
-- where polrelid = 'public.audit_logs'::regclass;
--   --> "Users can read own audit logs" (cmd=r / SELECT)

-- 4. Test insert via service_role (werkt altijd):
-- insert into public.audit_logs (user_id, action, ip_address, metadata)
-- values (null, 'test.ping', '127.0.0.1', '{"note":"handmatige test"}');
-- select * from public.audit_logs order by created_at desc limit 1;
--   --> 1 rij zichtbaar

-- 5. Test als authenticated user (vervang :uid door echte uuid):
-- set local role authenticated;
-- set local request.jwt.claim.sub = ':uid';
-- select count(*) from public.audit_logs;
--   --> Alleen eigen rijen, niet van andere users


-- ============================================================================
-- ROLLBACK (commented out)
-- ============================================================================
-- drop policy if exists "Users can read own audit logs" on public.audit_logs;
-- drop table if exists public.audit_logs;
