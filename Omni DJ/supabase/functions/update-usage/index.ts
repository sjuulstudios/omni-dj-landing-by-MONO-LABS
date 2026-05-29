/**
 * update-usage  Supabase Edge Function (Deno runtime).
 *
 * Server-side quota bookkeeping for the Omni DJ desktop bundle.
 * The shipped .app cannot hold SUPABASE_SERVICE_ROLE_KEY, so all
 * quota reads, rolling-window resets and increments are routed
 * through this function. JWT verification is REQUIRED.
 *
 * Flow:
 *   Bundle .app   POST /functions/v1/update-usage  this function
 *     (user JWT)                                     SERVICE_ROLE
 *                                                    profiles row
 *
 * POST body:    { action: "get" | "increment" }
 * Header:       Authorization: Bearer <supabase access token>
 *
 * Responses:
 *   action=get -> {
 *       ok: true,
 *       profile: { id, plan, usage_this_period, quota_reset_date, ... },
 *       plan, used, limit, remaining, reset_date, reset_in_days
 *   }
 *   action=increment -> {
 *       ok: true,
 *       used: <new usage_this_period>
 *   }
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

const SUPABASE_URL = Deno.env.get('SUPABASE_URL') ?? '';
const SUPABASE_ANON_KEY = Deno.env.get('SUPABASE_ANON_KEY') ?? '';
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '';

if (!SUPABASE_SERVICE_ROLE_KEY) {
  console.error('SUPABASE_SERVICE_ROLE_KEY ontbreekt  quota-updates zullen falen');
}

const PLAN_LIMITS: Record<string, number> = {
  free: 2,
  pro: 10,
  studio: Number.POSITIVE_INFINITY,
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
    const s = value.endsWith('Z') ? value : value;
    const d = new Date(s);
    return Number.isNaN(d.getTime()) ? null : d;
  } catch {
    return null;
  }
}

function buildSnapshot(profile: Record<string, unknown>) {
  const planRaw = String(profile.plan ?? 'free').toLowerCase();
  const plan = PLAN_LIMITS[planRaw] !== undefined ? planRaw : 'free';
  const limit = PLAN_LIMITS[plan];
  const used = Number(profile.usage_this_period ?? 0) || 0;
  const remaining = limit === Number.POSITIVE_INFINITY ? null : Math.max(0, limit - used);
  const resetDate = parsePgTimestamp(profile.quota_reset_date as string | null);
  const now = new Date();
  const resetInDays =
    resetDate === null ? null : Math.max(0, Math.floor((resetDate.getTime() - now.getTime()) / 86400000));
  return {
    profile,
    plan,
    used,
    limit: limit === Number.POSITIVE_INFINITY ? null : limit,
    remaining,
    reset_date: profile.quota_reset_date ?? null,
    reset_in_days: resetInDays,
  };
}

async function readAndRollProfile(serviceClient: ReturnType<typeof createClient>, userId: string) {
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
  if (!['get', 'increment'].includes(action)) {
    return jsonError(400, `Unknown action '${action}'. Expected 'get' or 'increment'.`);
  }

  if (action === 'get') {
    const result = await readAndRollProfile(serviceClient, userId);
    if (!result.ok) return jsonError(500, result.error);
    return jsonResponse(200, { ok: true, ...buildSnapshot(result.profile) });
  }

  // action === 'increment'  read current, write +1.
  // Acceptable race profile for a one-user-per-machine local app, same as
  // the Python-side _increment_usage. Swap for an RPC if multi-device.
  const result = await readAndRollProfile(serviceClient, userId);
  if (!result.ok) return jsonError(500, result.error);
  const cur = Number((result.profile as { usage_this_period?: number }).usage_this_period ?? 0) || 0;
  const newVal = cur + 1;
  const { error: incErr } = await serviceClient
    .from('profiles')
    .update({ usage_this_period: newVal })
    .eq('id', userId);
  if (incErr) {
    return jsonError(500, `quota increment failed: ${incErr.message}`);
  }
  return jsonResponse(200, { ok: true, used: newVal });
});
