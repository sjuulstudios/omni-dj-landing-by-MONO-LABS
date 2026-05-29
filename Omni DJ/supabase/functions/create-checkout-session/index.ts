/**
 * create-checkout-session — Supabase Edge Function (Deno runtime).
 *
 * Wordt aangeroepen door de Omni DJ desktop-app om een Stripe Checkout
 * Session te maken zonder dat de STRIPE_SECRET_KEY in de gebundelde
 * .app/.exe hoeft te staan.
 *
 * Flow:
 *   Browser ──▶ Flask /api/billing/start ──▶ deze edge function
 *               (met user JWT)               ──▶ Stripe API
 *                                            ◀── { url }
 *   Browser ◀── { url } ◀───────────────────
 *
 * Verwacht POST body: { plan: "pro" | "studio", success_url, cancel_url }
 * Verwacht header:    Authorization: Bearer <supabase access token>
 *
 * Vereiste edge function secrets (zet via `supabase secrets set ...`):
 *   STRIPE_SECRET_KEY        sk_test_... / sk_live_...
 *   STRIPE_PRICE_ID_PRO      price_...
 *   STRIPE_PRICE_ID_STUDIO   price_...
 *   (SUPABASE_URL en SUPABASE_ANON_KEY zijn automatisch beschikbaar.)
 *
 * Deploy (met JWT verificatie — zonder --no-verify-jwt!):
 *   cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/Omni DJ"
 *   supabase functions deploy create-checkout-session
 *
 * Zonder JWT-verificatie zou iedereen een checkout-sessie kunnen starten
 * op naam van een willekeurige user. Niet doen.
 */

// @ts-ignore — Deno-style URL imports, resolved at deploy time.
import Stripe from 'https://esm.sh/stripe@14.25.0?target=deno&deno-std=0.208.0';
// @ts-ignore
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.39.0';

declare const Deno: {
  env: { get(key: string): string | undefined };
  serve: (handler: (req: Request) => Response | Promise<Response>) => void;
};

// ─── Env ────────────────────────────────────────────────────────────────────

const STRIPE_SECRET_KEY = Deno.env.get('STRIPE_SECRET_KEY') ?? '';
const STRIPE_PRICE_ID_PRO = Deno.env.get('STRIPE_PRICE_ID_PRO') ?? '';
const STRIPE_PRICE_ID_STUDIO = Deno.env.get('STRIPE_PRICE_ID_STUDIO') ?? '';
const SUPABASE_URL = Deno.env.get('SUPABASE_URL') ?? '';
const SUPABASE_ANON_KEY = Deno.env.get('SUPABASE_ANON_KEY') ?? '';

if (!STRIPE_SECRET_KEY) {
  console.error('STRIPE_SECRET_KEY ontbreekt — checkout-creatie zal falen');
}

const stripe = new Stripe(STRIPE_SECRET_KEY, {
  apiVersion: '2024-06-20',
  httpClient: Stripe.createFetchHttpClient(),
});

// ─── CORS — Flask app draait op localhost en kan via browser ─────────────── #
//                                                                            #
//   In productie roept Flask (server-side) deze edge function aan, dus       #
//   CORS is dan niet nodig. Maar laat het wel toe, zodat een eventuele       #
//   directe browser-call vanuit een toekomstige web-only versie ook werkt.   #

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, content-type, x-client-info, apikey',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
};

function jsonError(status: number, message: string): Response {
  return new Response(JSON.stringify({ ok: false, error: message }), {
    status,
    headers: { ...corsHeaders, 'content-type': 'application/json' },
  });
}

// ─── HTTP entry point ───────────────────────────────────────────────────── #

Deno.serve(async (req: Request) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }
  if (req.method !== 'POST') {
    return jsonError(405, 'Method not allowed');
  }

  // 1. Authenticate caller — Supabase JWT vereist.
  const auth = req.headers.get('Authorization');
  if (!auth) return jsonError(401, 'Missing Authorization header');
  const token = auth.replace(/^Bearer\s+/i, '').trim();
  if (!token) return jsonError(401, 'Missing bearer token');

  const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
    global: { headers: { Authorization: `Bearer ${token}` } },
    auth: { persistSession: false, autoRefreshToken: false },
  });

  const { data: userData, error: userErr } = await supabase.auth.getUser(token);
  if (userErr || !userData?.user) {
    return jsonError(401, 'Invalid or expired token');
  }
  const user = userData.user;

  // 2. Parse and validate body.
  let body: Record<string, unknown>;
  try {
    body = await req.json();
  } catch {
    return jsonError(400, 'Body must be JSON');
  }

  const plan = String(body.plan ?? '').toLowerCase();
  const success_url = String(body.success_url ?? '');
  const cancel_url = String(body.cancel_url ?? '');

  let price_id: string | null = null;
  if (plan === 'pro') price_id = STRIPE_PRICE_ID_PRO;
  if (plan === 'studio') price_id = STRIPE_PRICE_ID_STUDIO;
  if (!price_id) return jsonError(400, `Onbekend plan '${plan}'. Verwacht 'pro' of 'studio'.`);
  if (!success_url) return jsonError(400, 'success_url ontbreekt');
  if (!cancel_url) return jsonError(400, 'cancel_url ontbreekt');

  // 3. Bestaande Stripe-customer ophalen indien aanwezig (re-checkout).
  let stripeCustomerId: string | null = null;
  try {
    const { data: profile } = await supabase
      .from('profiles')
      .select('stripe_customer_id')
      .eq('id', user.id)
      .maybeSingle();
    if (profile?.stripe_customer_id) {
      stripeCustomerId = profile.stripe_customer_id;
    }
  } catch (e) {
    // Niet fataal — als profiel-lookup faalt, behandelen we als nieuwe klant.
    console.warn('profile lookup failed', e);
  }

  // 4. Stripe Checkout Session aanmaken.
  const params: Stripe.Checkout.SessionCreateParams = {
    mode: 'subscription',
    line_items: [{ price: price_id, quantity: 1 }],
    client_reference_id: user.id,
    metadata: { user_id: user.id, plan },
    subscription_data: {
      metadata: { user_id: user.id, plan },
    },
    success_url,
    cancel_url,
    allow_promotion_codes: true,
    billing_address_collection: 'auto',
  };

  if (stripeCustomerId) {
    params.customer = stripeCustomerId;
    params.customer_update = { address: 'auto', name: 'auto' };
  } else {
    params.customer_email = user.email ?? undefined;
    // Stripe Tax later inschakelen wanneer MONO LABS VAT-NL geverifieerd is.
    params.automatic_tax = { enabled: false };
  }

  try {
    const session = await stripe.checkout.sessions.create(params);
    return new Response(
      JSON.stringify({ ok: true, url: session.url, session_id: session.id }),
      {
        status: 200,
        headers: { ...corsHeaders, 'content-type': 'application/json' },
      },
    );
  } catch (e) {
    const message = e instanceof Error ? e.message : String(e);
    console.error('Stripe checkout creation failed', message);
    return jsonError(500, `Stripe error: ${message}`);
  }
});
