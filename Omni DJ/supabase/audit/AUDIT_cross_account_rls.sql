-- AUDIT_cross_account_rls.sql
-- SESSIE 71 (2026-06-02) — VERPLICHTE data-isolatie-audit voor A1 (PLAN v1.3 sectie 7).
--
-- Doel: bewijzen dat geen enkele rij van workspace A zichtbaar is voor een user die
-- alleen lid is van workspace B. Catastrofale impact-categorie, dus dit MOET groen
-- zijn op een Supabase-branch VOORDAT 005-009 naar main mergen.
--
-- Werking: we seeden 2 workspaces (owned door 2 verschillende bestaande users) als
-- de tabel-owner (RLS wordt door de owner omzeild = veilige seed). Daarna
-- impersonaten we elke user via de Supabase-standaard (role 'authenticated' +
-- request.jwt.claims.sub) en tellen wat ze ZIEN. Elke lek = RAISE EXCEPTION.
-- Alles in EEN transactie met ROLLBACK aan het eind: de DB blijft schoon.
--
-- Draaien op de branch (psql of mcp execute_sql). Past de impersonatie-aanpak toe
-- die ook door supabase getest is; als de lokale rolnaam afwijkt, pas 'authenticated' aan.
-- Breid onderaan uit met dj_profiles + scheduled_posts volgens hetzelfde patroon.

begin;

-- ---------------------------------------------------------------------------
-- 0) Kies twee verschillende test-users (bestaande profielen). Vul desgewenst
--    vaste UUIDs in i.p.v. de auto-selectie.
-- ---------------------------------------------------------------------------
create temporary table _audit_users on commit drop as
  select id, row_number() over (order by created_at) as rn
  from public.profiles
  order by created_at
  limit 2;

do $$
declare n int;
begin
  select count(*) into n from _audit_users;
  if n < 2 then
    raise exception 'AUDIT: minstens 2 profielen nodig om isolatie te testen (gevonden: %)', n;
  end if;
end $$;

-- ---------------------------------------------------------------------------
-- 1) Seed als owner (RLS bypassed): 1 workspace + 1 clip per user.
-- ---------------------------------------------------------------------------
create temporary table _audit_ws (uid uuid, ws uuid, tag text) on commit drop;

do $$
declare ua uuid; ub uuid; wa uuid; wb uuid;
begin
  select id into ua from _audit_users where rn = 1;
  select id into ub from _audit_users where rn = 2;

  insert into public.workspaces (name, owner_id, artist_name) values ('AUDIT A', ua, 'AUDIT A') returning id into wa;
  insert into public.workspaces (name, owner_id, artist_name) values ('AUDIT B', ub, 'AUDIT B') returning id into wb;
  insert into _audit_ws values (ua, wa, 'A'), (ub, wb, 'B');

  insert into public.clips (workspace_id, label, source_set) values (wa, 'AUDIT clip A', 'setA');
  insert into public.clips (workspace_id, label, source_set) values (wb, 'AUDIT clip B', 'setB');
end $$;

-- ---------------------------------------------------------------------------
-- 2) Impersoneer user A en assert: ziet ALLEEN A, NOOIT B.
-- ---------------------------------------------------------------------------
do $$
declare ua uuid; wa uuid; wb uuid;
        seen_ws int; seen_other_ws int; seen_clip int; seen_other_clip int;
begin
  select uid into ua from _audit_ws where tag = 'A';
  select ws  into wa from _audit_ws where tag = 'A';
  select ws  into wb from _audit_ws where tag = 'B';

  perform set_config('request.jwt.claims', json_build_object('sub', ua, 'role','authenticated')::text, true);
  set local role authenticated;

  select count(*) into seen_ws        from public.workspaces where id = wa;
  select count(*) into seen_other_ws  from public.workspaces where id = wb;
  select count(*) into seen_clip      from public.clips where workspace_id = wa;
  select count(*) into seen_other_clip from public.clips where workspace_id = wb;

  reset role;  -- terug naar de seed-rol voor de assert/raise

  if seen_ws <> 1 then raise exception 'AUDIT FAIL: user A ziet eigen workspace niet (%).', seen_ws; end if;
  if seen_other_ws <> 0 then raise exception 'AUDIT LEAK: user A ziet workspace B (% rijen)!', seen_other_ws; end if;
  if seen_clip <> 1 then raise exception 'AUDIT FAIL: user A ziet eigen clip niet (%).', seen_clip; end if;
  if seen_other_clip <> 0 then raise exception 'AUDIT LEAK: user A ziet clips van B (% rijen)!', seen_other_clip; end if;
  raise notice 'AUDIT OK: user A isolatie groen.';
end $$;

-- ---------------------------------------------------------------------------
-- 3) Impersoneer user B en assert: ziet ALLEEN B, NOOIT A.
-- ---------------------------------------------------------------------------
do $$
declare ub uuid; wa uuid; wb uuid;
        seen_ws int; seen_other_ws int; seen_clip int; seen_other_clip int;
begin
  select uid into ub from _audit_ws where tag = 'B';
  select ws  into wa from _audit_ws where tag = 'A';
  select ws  into wb from _audit_ws where tag = 'B';

  perform set_config('request.jwt.claims', json_build_object('sub', ub, 'role','authenticated')::text, true);
  set local role authenticated;

  select count(*) into seen_ws        from public.workspaces where id = wb;
  select count(*) into seen_other_ws  from public.workspaces where id = wa;
  select count(*) into seen_clip      from public.clips where workspace_id = wb;
  select count(*) into seen_other_clip from public.clips where workspace_id = wa;

  reset role;

  if seen_ws <> 1 then raise exception 'AUDIT FAIL: user B ziet eigen workspace niet (%).', seen_ws; end if;
  if seen_other_ws <> 0 then raise exception 'AUDIT LEAK: user B ziet workspace A (% rijen)!', seen_other_ws; end if;
  if seen_clip <> 1 then raise exception 'AUDIT FAIL: user B ziet eigen clip niet (%).', seen_clip; end if;
  if seen_other_clip <> 0 then raise exception 'AUDIT LEAK: user B ziet clips van A (% rijen)!', seen_other_clip; end if;
  raise notice 'AUDIT OK: user B isolatie groen.';
end $$;

-- Geen wijzigingen behouden: dit is puur een test.
rollback;

-- Als beide "AUDIT OK"-notices verschijnen en er geen EXCEPTION is, is de
-- isolatie voor workspaces + clips bewezen. Herhaal hetzelfde patroon voor
-- dj_profiles, dj_templates en scheduled_posts vóór de merge naar main.
