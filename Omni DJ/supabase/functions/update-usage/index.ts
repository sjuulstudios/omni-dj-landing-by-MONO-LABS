/**
 * update-usage  Supabase Edge Function (Deno runtime).
 *
 * Server-side quota bookkeeping for the Omni DJ desktop bundle.
 * The shipped .app cannot hold SUPABASE_SERVICE_ROLE_KEY, so all
 * quota reads, reservations and releases are routed through this
 * function. JWT verification is REQUIRED.
 *
 * SESSIE 83 (2026-06-11) - rewritten per PLAN-QUOTA-PAYMENT-HARDENING:
 *   - Plan limits now come from the `plan_config` table (single source
 *     of truth), not a hardcoded constant.
 *   - Counting is atomic via the reserve_quota / release_quota /
 *     finalise_quota Postgres RPCs (migration 012). No more
 *     read-modify-write races.
 *   - New actions: `reserve` and `release` and `finalize` (all take a
 *     job_id) alongside the existing `get`.
 *   - `increment` is kept as a backward-compatibility alias for older
 *     DMGs in the field: it reserves under a synthetic job id and
 *     returns the old `{ ok, used }` shape.
 *
 * POST body: { action: "get" | "reserve" | "release" | "finalize" | "increment",
 *              job_id?: string }
 * Header:    Authorization: Bearer <supabase access token>
 *
 * Deploy (WITH JWT verification, no --no-verify-jwt):
 *   cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/Omni DJ"
 *   supabase functions deploy update-usage
 */

// @ts-ignore  Deno-style URL imports, resolved at deploy time.
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.39.0';

declare const Deno: {
  env: { get(key: string): string | undefined };
  serve: (handler: (req: Request) => Response | Promise<Response>) => void;
};
declare const crypto: { randomUUID(): string };

const SUPABASE_URL = Deno.env.get('SUPABASE_URL') ?? '';
const SUPABASE_ANON_KEY = Deno.env.get('SUPABASE_ANON_KEY') ?? '';
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '';

if (!SUPABASE_SERVICE_ROLE_KEY) {
  console.error('SUPABASE_SERVICE_ROLE_KEY ontbreekt  quota-updates zullen falen');
}

// Fallback only for the degraded case where plan_config cannot be read.
// The authoritative numbers live in the plan_config table.
const FALLBACK_LIMITS: Record<string, number | null> = {
  free: 2,
  pro: 10,
  studio: null,
};

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, content-type, x-client-info, apikey',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
};

function jsonResponse(status: number, body: Record<string, unknown>): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...corsHeaders, 'content-type': 'application/json' },
  });
}

function jsonError(status: number, message: string): Response {
  return jsonResponse(status, { ok: false, error: message });
}

function parsePgTimestamp(value: string | null | undefined): Date | null {
  if (!value) return null;
  try {
    const d = new Date(value);
    return Number.isNaN(d.getTime()) ? null : d;
  } catch {
    return null;
  }
}

type ServiceClient = ReturnType<typeof createClient>;

/** Read plan limits from plan_config. NULL monthly_limit means unlimited. */
async function loadPlanLimits(serviceClient: ServiceClient): Promise<Record<string, number | null>> {
  const { data, error } = await serviceClient.from('plan_config').select('plan, monthly_limit');
  if (error || !data || data.length === 0) {
    console.warn('plan_config read failed, using fallback limits', error?.message);
    return { ...FALLBACK_LIMITS };
  }
  const map: Record<string, number | null> = {};
  for (const row of data as Array<{ plan: string; monthly_limit: number | null }>) {
    map[String(row.plan).toLowerCase()] = row.monthly_limit;
  }
  return map;
}

function buildSnapshot(profile: Record<string, unknown>, limits: Record<string, number | null>) {
  const planRaw = String(profile.plan ?? 'free').toLowerCase();
  const plan = planRaw in limits ? planRaw : 'free';
  const limit = plan in limits ? limits[plan] : FALLBACK_LIMITS.free;
  const used = Number(profile.usage_this_period ?? 0) || 0;
  const remaining = limit === null || limit === undefined ? null : Math.max(0, limit - used);
  const resetDate = parsePgTimestamp(profile.quota_reset_date as string | null);
  const now = new Date();
  const resetInDays =
    resetDate === null ? null : Math.max(0, Math.floor((resetDate.getTime() - now.getTime()) / 86400000));
  return {
    profile,
    plan,
    used,
    limit: limit ?? null,
    remaining,
    reset_date: profile.quota_reset_date ?? null,
    reset_in_days: resetInDays,
  };
}

/** Read the profile and roll the 30-day window if expired (get-path only;
 * reserve/release roll the window inside the RPC). */
async function readAndRollProfile(serviceClient: ServiceClient, userId: string) {
  const { data: profile, error } = await serviceClient
    .from('profiles')
    .select('*')
    .eq('id', userId)
    .single();
  if (error) {
    return { ok: false as const, error: `profile read failed: ${error.message}` };
  }
  if (!profile) {
    return { ok: false as const, error: 'profile not found' };
  }
  const resetDate = parsePgTimestamp((profile as { quota_reset_date?: string }).quota_reset_date ?? null);
  const now = new Date();
  if (resetDate && now >= resetDate) {
    let newReset = new Date(resetDate.getTime() + 30 * 86400000);
    while (newReset <= now) newReset = new Date(newReset.getTime() + 30 * 86400000);
    const { error: updErr } = await serviceClient
      .from('profiles')
      .update({
        usage_this_period: 0,
        quota_reset_date: newReset.toISOString(),
      })
      .eq('id', userId);
    if (!updErr) {
      (profile as Record<string, unknown>).usage_this_period = 0;
      (profile as Record<string, unknown>).quota_reset_date = newReset.toISOString();
    } else {
      console.warn('Quota reset failed for', userId, updErr.message);
    }
  }
  return { ok: true as const, profile: profile as Record<string, unknown> };
}

/** Call one of the migration-012 quota RPCs and unwrap the jsonb result. */
async function callQuotaRpc(
  serviceClient: ServiceClient,
  fn: 'reserve_quota' | 'release_quota' | 'finalise_quota',
  userId: string,
  jobId: string,
): Promise<{ ok: boolean; [key: string]: unknown }> {
  const { data, error } = await serviceClient.rpc(fn, { p_user: userId, p_job: jobId });
  if (error) {
    return { ok: false, error: `${fn} failed: ${error.message}` };
  }
  if (data && typeof data === 'object') {
    return data as { ok: boolean; [key: string]: unknown };
  }
  return { ok: false, error: `${fn} returned an unexpected payload` };
}

Deno.serve(async (req: Request) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }
  if (req.method !== 'POST') {
    return jsonError(405, 'Method not allowed');
  }

  const auth = req.headers.get('Authorization');
  if (!auth) return jsonError(401, 'Missing Authorization header');
  const token = auth.replace(/^Bearer\s+/i, '').trim();
  if (!token) return jsonError(401, 'Missing bearer token');

  // Verify the JWT using the anon-key client.
  const anonClient = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
    global: { headers: { Authorization: `Bearer ${token}` } },
    auth: { persistSession: false, autoRefreshToken: false },
  });
  const { data: userData, error: userErr } = await anonClient.auth.getUser(token);
  if (userErr || !userData?.user) {
    return jsonError(401, 'Invalid or expired token');
  }
  const userId = userData.user.id;

  // Privileged client for quota mutations  uses SERVICE_ROLE so the
  // bundled .app never sees it.
  const serviceClient = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, {
    auth: { persistSession: false, autoRefreshToken: false },
  });

  let body: Record<string, unknown>;
  try {
    body = await req.json();
  } catch {
    return jsonError(400, 'Body must be JSON');
  }
  const action = String(body.action ?? '').toLowerCase();
  const validActions = ['get', 'reserve', 'release', 'finalize', 'finalise', 'increment'];
  if (!validActions.includes(action)) {
    return jsonError(400, `Unknown action '${action}'. Expected one of: ${validActions.join(', ')}.`);
  }

  if (action === 'get') {
    const result = await readAndRollProfile(serviceClient, userId);
    if (!result.ok) return jsonError(500, result.error);
    const limits = await loadPlanLimits(serviceClient);
    return jsonResponse(200, { ok: true, ...buildSnapshot(result.profile, limits) });
  }

  if (action === 'reserve' || action === 'release' || action === 'finalize' || action === 'finalise') {
    const jobId = String(body.job_id ?? '').trim();
    if (!jobId) return jsonError(400, `Action '${action}' requires a job_id`);
    const fn = action === 'reserve' ? 'reserve_quota'
             : action === 'release' ? 'release_quota'
             : 'finalise_quota';
    const res = await callQuotaRpc(serviceClient, fn, userId, jobId);
    if (!res.ok) return jsonError(500, String(res.error ?? `${action} failed`));
    return jsonResponse(200, res);
  }

  // action === 'increment'  backward-compatibility alias for older DMGs.
  // Old clients call this once at the END of a successful analysis and only
  // read `used` back. We map it onto a reserve under a synthetic job id so
  // the counting still goes through the atomic RPC. If the user is at their
  // limit the reserve refuses and `used` simply stays where it was, which
  // is strictly fairer than the old unconditional increment.
  const legacyJob = `legacy-${crypto.randomUUID()}`;
  const res = await callQuotaRpc(serviceClient, 'reserve_quota', userId, legacyJob);
  if (!res.ok) return jsonError(500, String(res.error ?? 'increment failed'));
  return jsonResponse(200, { ok: true, used: Number(res.used ?? 0) });
});
