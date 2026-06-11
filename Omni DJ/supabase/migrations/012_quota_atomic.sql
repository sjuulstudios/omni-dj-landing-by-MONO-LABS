-- 012_quota_atomic.sql
-- SESSIE 83 (2026-06-11) - Quota + payment hardening, Fase 1.
-- Zie PLAN-QUOTA-PAYMENT-HARDENING-2026-06-11.md (issues A, B, C).
--
-- STATUS: TOEGEPAST op main (lbabsffxefkrxwzkbzar) 2026-06-11, na groene
-- wegwerp-branch-audit (11 RPC-asserties in tests/test_quota_rpc.sql +
-- RLS-isolatie nieuwe tabellen + service_role-execute-check).
--
-- Wat dit doet:
--   1. plan_config: 1 bron van waarheid voor de maandlimieten per plan.
--      NULL = onbeperkt. Wijzigen = 1 SQL update, geen DMG-rebuild.
--   2. quota_reservations: per-job reservering (reserved/finalised/released)
--      zodat reserve/release idempotent zijn en een mid-flight planwissel
--      nooit dubbel telt of verkeerd blokkeert.
--   3. reserve_quota / release_quota / finalise_quota: atomaire RPC's.
--      reserve_quota lockt de profiles-rij (FOR UPDATE), dus twee parallelle
--      starts kunnen nooit allebei "nog 1 plek" zien (fix A + B).
--
-- Beveiliging:
--   - RPC's zijn ALLEEN door service_role aanroepbaar (edge function +
--     supabase_admin in dev). anon/authenticated kunnen hun eigen teller
--     dus niet via /rest/v1/rpc manipuleren.
--   - plan_config is leesbaar voor anon + authenticated (niet geheim),
--     schrijfbaar alleen via service_role.
--   - quota_reservations: gebruiker mag alleen EIGEN rijen lezen.

-- ---------------------------------------------------------------------------
-- 1) plan_config
-- ---------------------------------------------------------------------------

create table if not exists public.plan_config (
  plan          text primary key,
  monthly_limit integer,                -- NULL betekent onbeperkt
  updated_at    timestamptz not null default now()
);

insert into public.plan_config (plan, monthly_limit) values
  ('free',   2),
  ('pro',    10),
  ('studio', null)
on conflict (plan) do nothing;

alter table public.plan_config enable row level security;

drop policy if exists plan_config_read on public.plan_config;
create policy plan_config_read on public.plan_config
  for select to anon, authenticated using (true);

-- Geen insert/update/delete policies: alleen service_role (bypasst RLS)
-- mag limieten wijzigen. Verb-grants ook dichtzetten voor de zekerheid.
revoke insert, update, delete on table public.plan_config from anon, authenticated;

-- ---------------------------------------------------------------------------
-- 2) quota_reservations
-- ---------------------------------------------------------------------------

create table if not exists public.quota_reservations (
  job_id     text primary key,
  user_id    uuid not null references auth.users(id) on delete cascade,
  state      text not null default 'reserved'
             check (state in ('reserved', 'finalised', 'released')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists quota_reservations_user_idx
  on public.quota_reservations (user_id, created_at desc);

alter table public.quota_reservations enable row level security;

drop policy if exists quota_reservations_select_own on public.quota_reservations;
create policy quota_reservations_select_own on public.quota_reservations
  for select to authenticated using (user_id = auth.uid());

-- Mutaties lopen uitsluitend via de RPC's (service_role).
revoke insert, update, delete on table public.quota_reservations from anon, authenticated;

-- ---------------------------------------------------------------------------
-- 3) reserve_quota: window-roll + limietcheck + reservering, in 1 transactie
-- ---------------------------------------------------------------------------

create or replace function public.reserve_quota(p_user uuid, p_job text)
returns jsonb
language plpgsql
set search_path = public
as $$
declare
  v_plan      text;
  v_limit     integer;
  v_used      integer;
  v_now       timestamptz := now();
  v_reset     timestamptz;
  v_state     text;
  v_res_user  uuid;
  v_allowed   boolean;
  v_days      integer;
begin
  if p_user is null or p_job is null or length(trim(p_job)) = 0 then
    return jsonb_build_object('ok', false, 'error', 'missing user or job id');
  end if;

  -- Lock de profielrij: serialiseert alle quota-beslissingen per gebruiker.
  select lower(trim(coalesce(plan, 'free'))),
         coalesce(usage_this_period, 0),
         quota_reset_date
    into v_plan, v_used, v_reset
    from profiles where id = p_user for update;
  if not found then
    return jsonb_build_object('ok', false, 'error', 'profile not found');
  end if;

  -- Rolling 30-dagen window (zelfde logica als de oude edge function).
  if v_reset is null then
    v_reset := v_now + interval '30 days';
    update profiles set quota_reset_date = v_reset where id = p_user;
  elsif v_now >= v_reset then
    while v_reset <= v_now loop
      v_reset := v_reset + interval '30 days';
    end loop;
    update profiles
       set usage_this_period = 0, quota_reset_date = v_reset
     where id = p_user;
    v_used := 0;
  end if;

  -- Limiet uit plan_config (NULL = onbeperkt). Onbekend plan telt als free.
  select monthly_limit into v_limit
    from plan_config where plan = v_plan;
  if not found then
    v_plan := 'free';
    select monthly_limit into v_limit
      from plan_config where plan = 'free';
    if not found then
      v_limit := 2;  -- laatste vangnet als plan_config leeg zou zijn
    end if;
  end if;
  v_days := greatest(0, floor(extract(epoch from (v_reset - v_now)) / 86400))::int;

  -- Idempotentie: bestaande reservering voor deze job.
  select state, user_id into v_state, v_res_user
    from quota_reservations where job_id = p_job;
  if found then
    if v_res_user is distinct from p_user then
      return jsonb_build_object('ok', false, 'error', 'job belongs to another user');
    end if;
    if v_state in ('reserved', 'finalised') then
      -- Al gereserveerd of al afgerond: zelfde beslissing teruggeven,
      -- NIET nogmaals tellen.
      return jsonb_build_object(
        'ok', true, 'allowed', true, 'already', true,
        'job_state', v_state, 'plan', v_plan, 'used', v_used,
        'limit', v_limit,
        'remaining', case when v_limit is null then null
                          else greatest(0, v_limit - v_used) end,
        'reset_date', v_reset, 'reset_in_days', v_days);
    end if;
    -- v_state = 'released': een eerdere poging is vrijgegeven; een verse
    -- reserve-aanvraag voor dezelfde job telt opnieuw (retry-pad).
  end if;

  v_allowed := (v_limit is null) or (v_used < v_limit);

  if v_allowed then
    insert into quota_reservations (job_id, user_id, state)
    values (p_job, p_user, 'reserved')
    on conflict (job_id) do update
      set state = 'reserved', updated_at = now();
    v_used := v_used + 1;
    update profiles set usage_this_period = v_used where id = p_user;
  end if;

  return jsonb_build_object(
    'ok', true, 'allowed', v_allowed, 'already', false,
    'job_state', case when v_allowed then 'reserved' else null end,
    'plan', v_plan, 'used', v_used,
    'limit', v_limit,
    'remaining', case when v_limit is null then null
                      else greatest(0, v_limit - v_used) end,
    'reset_date', v_reset, 'reset_in_days', v_days);
end;
$$;

-- ---------------------------------------------------------------------------
-- 4) release_quota: mislukte of lege analyse geeft de plek terug. Idempotent.
-- ---------------------------------------------------------------------------

create or replace function public.release_quota(p_user uuid, p_job text)
returns jsonb
language plpgsql
set search_path = public
as $$
declare
  v_used integer;
begin
  if p_user is null or p_job is null or length(trim(p_job)) = 0 then
    return jsonb_build_object('ok', false, 'error', 'missing user or job id');
  end if;

  -- Zelfde lock-volgorde als reserve_quota (eerst profiles) tegen deadlocks.
  perform 1 from profiles where id = p_user for update;
  if not found then
    return jsonb_build_object('ok', false, 'error', 'profile not found');
  end if;

  update quota_reservations
     set state = 'released', updated_at = now()
   where job_id = p_job and user_id = p_user and state = 'reserved';

  if found then
    -- Floor op 0: na een webhook-reset mag release de teller nooit
    -- negatief duwen.
    update profiles
       set usage_this_period = greatest(coalesce(usage_this_period, 0) - 1, 0)
     where id = p_user
     returning usage_this_period into v_used;
    return jsonb_build_object('ok', true, 'released', true, 'used', v_used);
  end if;

  select usage_this_period into v_used from profiles where id = p_user;
  return jsonb_build_object('ok', true, 'released', false,
                            'used', coalesce(v_used, 0));
end;
$$;

-- ---------------------------------------------------------------------------
-- 5) finalise_quota: succesvolle analyse markeren. Geen tellerwijziging;
--    voorkomt alleen dat een latere (verdwaalde) release nog decrementeert.
-- ---------------------------------------------------------------------------

create or replace function public.finalise_quota(p_user uuid, p_job text)
returns jsonb
language plpgsql
set search_path = public
as $$
begin
  if p_user is null or p_job is null or length(trim(p_job)) = 0 then
    return jsonb_build_object('ok', false, 'error', 'missing user or job id');
  end if;

  update quota_reservations
     set state = 'finalised', updated_at = now()
   where job_id = p_job and user_id = p_user and state = 'reserved';

  return jsonb_build_object('ok', true, 'finalised', found);
end;
$$;

-- ---------------------------------------------------------------------------
-- 6) Grants: RPC's alleen voor service_role.
-- ---------------------------------------------------------------------------

revoke all on function public.reserve_quota(uuid, text)  from public, anon, authenticated;
revoke all on function public.release_quota(uuid, text)  from public, anon, authenticated;
revoke all on function public.finalise_quota(uuid, text) from public, anon, authenticated;

grant execute on function public.reserve_quota(uuid, text)  to service_role;
grant execute on function public.release_quota(uuid, text)  to service_role;
grant execute on function public.finalise_quota(uuid, text) to service_role;
