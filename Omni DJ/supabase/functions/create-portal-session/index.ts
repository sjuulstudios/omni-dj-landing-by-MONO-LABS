/**
 * create-portal-session — Supabase Edge Function (Deno runtime).
 *
 * Maakt een Stripe Customer Portal-sessie zodat een betalende user zijn
 * abonnement kan beheren (opzeggen, plan wijzigen, kaart updaten,
 * facturen bekijken) — zonder dat Sjuul Studios die UI zelf bouwt.
 *
 * Voor dezelfde reden als create-checkout-session: STRIPE_SECRET_KEY mag
 * niet in de gebundelde desktop-app staan, dus dit gaat via een edge
 * function met de JWT van de ingelogde user.
 *
 * Verwacht POST body: { return_url }
 * Verwacht header:    Authorization: Bearer <supabase access token>
 *
 * Vereiste edge function secrets:
 *   STRIPE_SECRET_KEY        sk_test_... / sk_live_...
 *
 * Deploy:
 *   cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/Omni DJ"
 *   supabase functions deploy create-portal-session
 */

// @ts-ignore
import Stripe from 'https://esm.sh/stripe@14.25.0?target=deno&deno-std=0.208.0';
// @ts-ignore
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.39.0';

declare const Deno: {
  env: { get(key: string): string | undefined };
  serve: (handler: (req: Request) => Response | Promise<Response>) => void;
};

const STRIPE_SECRET_KEY = Deno.env.get('STRIPE_SECRET_KEY') ?? '';
const SUPABASE_URL = Deno.env.get('SUPABASE_URL') ?? '';
const SUPABASE_ANON_KEY = Deno.env.get('SUPABASE_ANON_KEY') ?? '';

const stripe = new Stripe(STRIPE_SECRET_KEY, {
  apiVersion: '2024-06-20',
  httpClient: Stripe.createFetchHttpClient(),
});

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

  const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
    global: { headers: { Authorization: `Bearer ${token}` } },
    auth: { persistSession: false, autoRefreshToken: false },
  });

  const { data: userData, error: userErr } = await supabase.auth.getUser(token);
  if (userErr || !userData?.user) return jsonError(401, 'Invalid or expired token');
  const user = userData.user;

  let body: Record<string, unknown>;
  try {
    body = await req.json();
  } catch {
    return jsonError(400, 'Body must be JSON');
  }
  const return_url = String(body.return_url ?? '');
  if (!return_url) return jsonError(400, 'return_url ontbreekt');

  // Stripe customer ophalen uit profiles (RLS staat alleen eigen rij toe).
  const { data: profile, error: profErr } = await supabase
    .from('profiles')
    .select('stripe_customer_id')
    .eq('id', user.id)
    .maybeSingle();

  if (profErr) return jsonError(500, `Profile lookup failed: ${profErr.message}`);
  if (!profile?.stripe_customer_id) {
    return jsonError(400, 'Geen actief Stripe-abonnement gekoppeld aan deze account.');
  }

  try {
    const session = await stripe.billingPortal.sessions.create({
      customer: profile.stripe_customer_id,
      return_url,
    });
    return new Response(
      JSON.stringify({ ok: true, url: session.url }),
      {
        status: 200,
        headers: { ...corsHeaders, 'content-type': 'application/json' },
      },
    );
  } catch (e) {
    const message = e instanceof Error ? e.message : String(e);
    console.error('Stripe portal session creation failed', message);
    return jsonError(500, `Stripe error: ${message}`);
  }
});
