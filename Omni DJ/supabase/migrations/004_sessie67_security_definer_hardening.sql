-- 004_sessie67_security_definer_hardening.sql
-- SESSIE 67 (2026-05-31) — Supabase security-linter warnings oplossen (S3).
-- Reeds toegepast op het live project (lbabsffxefkrxwzkbzar) via apply_migration.
-- Hier vastgelegd voor version control.
--
-- Achtergrond: de Supabase security-advisor meldde 3 WARN-items:
--   1. handle_new_user()  — SECURITY DEFINER, aanroepbaar via /rest/v1/rpc door anon/authenticated
--   2. rls_auto_enable()  — idem (is een event-trigger functie, hoort nooit RPC-callable)
--   3. handle_updated_at() — mutable search_path
-- De 4e WARN (leaked password protection) is een Auth-dashboard-toggle, geen SQL.

-- 1+2) EXECUTE intrekken voor de exposed rollen. De triggers blijven werken,
--      want die draaien als functie-owner en niet via een rol-EXECUTE-grant.
revoke execute on function public.handle_new_user()  from anon, authenticated, public;
revoke execute on function public.rls_auto_enable()  from anon, authenticated, public;

-- 3) search_path vastzetten op leeg (functie gebruikt alleen now() + NEW).
alter function public.handle_updated_at() set search_path = '';
