-- tests/test_quota_rpc.sql
-- SESSIE 83 (2026-06-11) - SQL/RPC unit test voor migratie 012_quota_atomic.
-- Sectie 4 van PLAN-QUOTA-PAYMENT-HARDENING-2026-06-11.md (laag 1).
--
-- DRAAIEN OP EEN WEGWERP-BRANCH (of een testdatabase), NOOIT op main:
-- het script maakt 2 test-users aan en ruimt ze aan het einde weer op.
-- Elke assertie RAISEt een EXCEPTION bij falen; bij succes eindigt het
-- script met "ALLE QUOTA-RPC-TESTS GROEN". Verwacht vs. werkelijk wordt
-- per stap met RAISE NOTICE geprint.

do $$
declare
  u1 uuid := gen_random_uuid();
  u2 uuid := gen_random_uuid();
  r jsonb;
  v_used int;
  v_state text;
begin
  raise notice 'Test-users: u1=% u2=%', u1, u2;

  -- Setup: 2 auth-users. De handle_new_user-trigger maakt de profiles aan;
  -- zo niet (andere triggerconfig op de branch), dan vangen we dat op.
  insert into auth.users (id, email) values
    (u1, 'quota-rpc-test-1@example.com'),
    (u2, 'quota-rpc-test-2@example.com');
  insert into public.profiles (id, email) values
    (u1, 'quota-rpc-test-1@example.com'),
    (u2, 'quota-rpc-test-2@example.com')
  on conflict (id) do nothing;

  -- Uitgangssituatie scenario A: Free, used=1, window geldig.
  update public.profiles
     set plan = 'free', usage_this_period = 1,
         quota_reset_date = now() + interval '20 days'
   where id = u1;

  ------------------------------------------------------------------
  -- 1) reserve(jobA): toegestaan, teller 1 -> 2
  ------------------------------------------------------------------
  r := public.reserve_quota(u1, 'jobA');
  raise notice '1) reserve jobA: verwacht allowed=true used=2, werkelijk %', r;
  if not (r->>'allowed')::boolean or (r->>'used')::int <> 2 then
    raise exception 'TEST 1 FAALT: %', r;
  end if;

  ------------------------------------------------------------------
  -- 2) reserve(jobB): limiet bereikt (2/2), geweigerd, teller blijft 2
  ------------------------------------------------------------------
  r := public.reserve_quota(u1, 'jobB');
  raise notice '2) reserve jobB: verwacht allowed=false used=2, werkelijk %', r;
  if (r->>'allowed')::boolean or (r->>'used')::int <> 2 then
    raise exception 'TEST 2 FAALT: %', r;
  end if;
  select usage_this_period into v_used from public.profiles where id = u1;
  if v_used <> 2 then
    raise exception 'TEST 2 FAALT: teller in profiles is % (verwacht 2)', v_used;
  end if;

  ------------------------------------------------------------------
  -- 3) Idempotentie: reserve(jobA) nogmaals telt NIET dubbel
  ------------------------------------------------------------------
  r := public.reserve_quota(u1, 'jobA');
  raise notice '3) reserve jobA herhaald: verwacht allowed=true already=true used=2, werkelijk %', r;
  if not (r->>'allowed')::boolean or not (r->>'already')::boolean
     or (r->>'used')::int <> 2 then
    raise exception 'TEST 3 FAALT: %', r;
  end if;

  ------------------------------------------------------------------
  -- 4) Mid-analysis upgrade: webhook zet plan=pro, usage=0, vers window.
  --    Daarna: completion-pad telt NIETS bij (alleen finalise), en een
  --    nieuwe reserve(jobC) mag onder Pro.
  ------------------------------------------------------------------
  update public.profiles
     set plan = 'pro', usage_this_period = 0,
         quota_reset_date = now() + interval '30 days'
   where id = u1;
  r := public.finalise_quota(u1, 'jobA');
  raise notice '4a) finalise jobA na upgrade: verwacht finalised=true, werkelijk %', r;
  if not (r->>'finalised')::boolean then
    raise exception 'TEST 4a FAALT: %', r;
  end if;
  select usage_this_period into v_used from public.profiles where id = u1;
  raise notice '4b) teller na upgrade+finalise: verwacht 0, werkelijk %', v_used;
  if v_used <> 0 then
    raise exception 'TEST 4b FAALT: teller is % (verwacht 0, geen eind-increment)', v_used;
  end if;
  r := public.reserve_quota(u1, 'jobC');
  raise notice '4c) reserve jobC onder pro: verwacht allowed=true used=1 limit=10, werkelijk %', r;
  if not (r->>'allowed')::boolean or (r->>'used')::int <> 1
     or (r->>'limit')::int <> 10 or (r->>'plan') <> 'pro' then
    raise exception 'TEST 4c FAALT: %', r;
  end if;

  ------------------------------------------------------------------
  -- 5) Failure-pad: release(jobC) geeft de plek terug, idempotent
  ------------------------------------------------------------------
  r := public.release_quota(u1, 'jobC');
  raise notice '5a) release jobC: verwacht released=true used=0, werkelijk %', r;
  if not (r->>'released')::boolean or (r->>'used')::int <> 0 then
    raise exception 'TEST 5a FAALT: %', r;
  end if;
  r := public.release_quota(u1, 'jobC');
  raise notice '5b) release jobC herhaald: verwacht released=false used=0, werkelijk %', r;
  if (r->>'released')::boolean or (r->>'used')::int <> 0 then
    raise exception 'TEST 5b FAALT: %', r;
  end if;

  ------------------------------------------------------------------
  -- 6) Release na webhook-reset kan de teller nooit negatief duwen
  ------------------------------------------------------------------
  r := public.reserve_quota(u1, 'jobD');
  if not (r->>'allowed')::boolean then
    raise exception 'TEST 6 setup FAALT: %', r;
  end if;
  update public.profiles set usage_this_period = 0 where id = u1;  -- webhook-reset
  r := public.release_quota(u1, 'jobD');
  select usage_this_period into v_used from public.profiles where id = u1;
  raise notice '6) release na reset: verwacht used=0 (floor), werkelijk used=% rpc=%', v_used, r;
  if v_used < 0 or (r->>'used')::int < 0 then
    raise exception 'TEST 6 FAALT: teller negatief (%)', v_used;
  end if;

  ------------------------------------------------------------------
  -- 7) Verlopen window rolt automatisch binnen reserve
  ------------------------------------------------------------------
  update public.profiles
     set usage_this_period = 5, quota_reset_date = now() - interval '3 days'
   where id = u1;
  r := public.reserve_quota(u1, 'jobE');
  raise notice '7) reserve na verlopen window: verwacht allowed=true used=1 (gerold), werkelijk %', r;
  if not (r->>'allowed')::boolean or (r->>'used')::int <> 1 then
    raise exception 'TEST 7 FAALT: %', r;
  end if;
  select usage_this_period into v_used from public.profiles where id = u1;
  if v_used <> 1 then
    raise exception 'TEST 7 FAALT: teller is % (verwacht 1)', v_used;
  end if;

  ------------------------------------------------------------------
  -- 8) Studio (limit NULL) is onbeperkt
  ------------------------------------------------------------------
  update public.profiles set plan = 'studio', usage_this_period = 999 where id = u1;
  r := public.reserve_quota(u1, 'jobF');
  raise notice '8) reserve onder studio: verwacht allowed=true limit=null, werkelijk %', r;
  if not (r->>'allowed')::boolean or (r->'limit') <> 'null'::jsonb then
    raise exception 'TEST 8 FAALT: %', r;
  end if;

  ------------------------------------------------------------------
  -- 9) Onbekend plan valt terug op free-limiet
  ------------------------------------------------------------------
  update public.profiles set plan = 'goldmember', usage_this_period = 0 where id = u1;
  r := public.reserve_quota(u1, 'jobG');
  raise notice '9) reserve onder onbekend plan: verwacht plan=free limit=2, werkelijk %', r;
  if (r->>'plan') <> 'free' or (r->>'limit')::int <> 2 then
    raise exception 'TEST 9 FAALT: %', r;
  end if;

  ------------------------------------------------------------------
  -- 10) Cross-user guard: u2 kan andermans job niet claimen of releasen
  ------------------------------------------------------------------
  update public.profiles
     set plan = 'free', usage_this_period = 0,
         quota_reset_date = now() + interval '30 days'
   where id = u2;
  r := public.reserve_quota(u2, 'jobG');
  raise notice '10a) u2 reserve op jobG van u1: verwacht ok=false, werkelijk %', r;
  if (r->>'ok')::boolean then
    raise exception 'TEST 10a FAALT: %', r;
  end if;
  r := public.release_quota(u2, 'jobG');
  select usage_this_period into v_used from public.profiles where id = u1;
  raise notice '10b) u2 release op jobG: teller u1 verwacht 1, werkelijk %', v_used;
  if v_used <> 1 then
    raise exception 'TEST 10b FAALT: teller u1 is % (cross-user release lekte)', v_used;
  end if;

  ------------------------------------------------------------------
  -- 11) Reserveringsstaten kloppen in de tabel
  ------------------------------------------------------------------
  select state into v_state from public.quota_reservations where job_id = 'jobA';
  if v_state <> 'finalised' then
    raise exception 'TEST 11 FAALT: jobA state=% (verwacht finalised)', v_state;
  end if;
  select state into v_state from public.quota_reservations where job_id = 'jobC';
  if v_state <> 'released' then
    raise exception 'TEST 11 FAALT: jobC state=% (verwacht released)', v_state;
  end if;

  -- Opruimen
  delete from public.quota_reservations where user_id in (u1, u2);
  delete from public.profiles where id in (u1, u2);
  delete from auth.users where id in (u1, u2);

  raise notice 'ALLE QUOTA-RPC-TESTS GROEN';
end $$;
