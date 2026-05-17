/**
 * Stripe webhook — Supabase Edge Function (Deno runtime).
 *
 * Receives subscription events from Stripe and mirrors them into the
 * `profiles` table so the Flask app sees the user's plan change.
 *
 * Events handled:
 *   - checkout.session.completed         → first paid checkout
 *   - customer.subscription.updated      → plan change, trial→active, etc.
 *   - customer.subscription.deleted      → user cancelled (after period end)
 *   - invoice.payment_failed             → logged, no DB write (Stripe retries)
 *
 * Required edge function secrets (set via `supabase secrets set ...`):
 *   STRIPE_SECRET_KEY        sk_test_... or sk_live_...
 *   STRIPE_WEBHOOK_SECRET    whsec_... (from Stripe dashboard → Developers
 *                            → Webhooks → click endpoint → Signing secret)
 *   STRIPE_PRICE_ID_PRO      price_... — used to map price → plan name
 *   STRIPE_PRICE_ID_STUDIO   price_...
 *   SUPABASE_SERVICE_ROLE_KEY  ECHT GEHEIM — bypasses RLS so we can update
 *                              any profile row.
 *   (SUPABASE_URL and SUPABASE_ANON_KEY are auto-injected by Supabase
 *   runtime — no need to set them manually.)
 *
 * Deploy:
 *   cd "/Users/sjuulsmits/Documents/Claude/Projects/Clip Live/dj-clip-cutter"
 *   supabase functions deploy stripe-webhook --no-verify-jwt
 *
 * The --no-verify-jwt flag is critical: Stripe doesn't send Supabase JWTs,
 * it sends its own signature in `stripe-signature`. We verify that below.
 */

// @ts-ignore — Deno-style URL imports, resolved at deploy time.
import Stripe from 'https://esm.sh/stripe@14.25.0?target=deno&deno-std=0.208.0';
// @ts-ignore
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.39.0';

// Deno globals — declared so this also type-checks in a Node-aware editor.
declare const Deno: {
  env: { get(key: string): string | undefined };
  serve: (handler: (req: Request) => Response | Promise<Response>) => void;
};

// ─── Env ────────────────────────────────────────────────────────────────────

const STRIPE_SECRET_KEY = Deno.env.get('STRIPE_SECRET_KEY') ?? '';
const STRIPE_WEBHOOK_SECRET = Deno.env.get('STRIPE_WEBHOOK_SECRET') ?? '';
const STRIPE_PRICE_ID_PRO = Deno.env.get('STRIPE_PRICE_ID_PRO') ?? '';
const STRIPE_PRICE_ID_STUDIO = Deno.env.get('STRIPE_PRICE_ID_STUDIO') ?? '';

const SUPABASE_URL = Deno.env.get('SUPABASE_URL') ?? '';
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '';

if (!STRIPE_SECRET_KEY || !STRIPE_WEBHOOK_SECRET) {
  console.error('Missing STRIPE_SECRET_KEY or STRIPE_WEBHOOK_SECRET — webhook will reject all events');
}
if (!SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY) {
  console.error('Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY — DB writes will fail');
}

const stripe = new Stripe(STRIPE_SECRET_KEY, {
  apiVersion: '2024-06-20',
  // Edge functions run on Deno, not Node — use Fetch API for HTTP.
  httpClient: Stripe.createFetchHttpClient(),
});

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, {
  auth: { persistSession: false, autoRefreshToken: false },
});

// ─── Helpers ────────────────────────────────────────────────────────────────

function planFromPriceId(priceId: string | null | undefined): 'pro' | 'studio' | null {
  if (!priceId) return null;
  if (priceId === STRIPE_PRICE_ID_PRO) return 'pro';
  if (priceId === STRIPE_PRICE_ID_STUDIO) return 'studio';
  return null;
}

/** Walk a Stripe Subscription to find which of our plans it represents.
 * Subscriptions can have multiple items but our products are single-item. */
function planFromSubscription(sub: Stripe.Subscription): 'pro' | 'studio' | null {
  const items = sub.items?.data ?? [];
  for (const item of items) {
    const plan = planFromPriceId(item.price?.id);
    if (plan) return plan;
  }
  return null;
}

/** Find a profile row by Stripe customer id. Used by subscription.updated/deleted
 * events where the only stable identifier is the customer. Returns null if
 * the customer isn't yet linked to any profile (shouldn't happen if
 * checkout.session.completed always fires first, but be defensive). */
async function findProfileByCustomerId(customerId: string) {
  const { data, error } = await supabase
    .from('profiles')
    .select('id, plan, stripe_customer_id, stripe_subscription_id')
    .eq('stripe_customer_id', customerId)
    .maybeSingle();
  if (error) {
    console.error('findProfileByCustomerId error', error);
    return null;
  }
  return data;
}

/** Compute a fresh quota_reset_date 30 days from now. */
function thirtyDaysFromNow(): string {
  const d = new Date();
  d.setUTCDate(d.getUTCDate() + 30);
  return d.toISOString();
}

// ─── Event handlers ─────────────────────────────────────────────────────────

async function handleCheckoutCompleted(session: Stripe.Checkout.Session) {
  // First successful checkout for a user. Pull user_id out of metadata
  // (we set this when creating the session in billing.py).
  const userId = session.metadata?.user_id || session.client_reference_id || null;
  if (!userId) {
    console.warn('checkout.session.completed without user_id metadata', session.id);
    return;
  }

  // Resolve which plan they bought. Cheapest path: look at the subscription
  // line items.
  let plan: 'pro' | 'studio' | null = null;
  let subscriptionId: string | null = null;

  if (session.subscription) {
    subscriptionId = typeof session.subscription === 'string'
      ? session.subscription
      : session.subscription.id;
    try {
      const sub = await stripe.subscriptions.retrieve(subscriptionId);
      plan = planFromSubscription(sub);
    } catch (e) {
      console.error('Could not retrieve subscription', subscriptionId, e);
    }
  }

  // Fallback to metadata.plan if the subscription lookup failed.
  if (!plan && session.metadata?.plan) {
    const m = session.metadata.plan.toLowerCase();
    if (m === 'pro' || m === 'studio') plan = m;
  }

  if (!plan) {
    console.warn('Could not determine plan for checkout', session.id);
    return;
  }

  const customerId = typeof session.customer === 'string'
    ? session.customer
    : session.customer?.id ?? null;

  const update: Record<string, unknown> = {
    plan,
    stripe_customer_id: customerId,
    stripe_subscription_id: subscriptionId,
    usage_this_period: 0,
    quota_reset_date: thirtyDaysFromNow(),
  };

  const { error } = await supabase.from('profiles').update(update).eq('id', userId);
  if (error) {
    console.error('Profile update failed (checkout.completed)', userId, error);
    throw error;
  }
  console.log(`Activated ${plan} for user ${userId} (sub ${subscriptionId})`);
}

async function handleSubscriptionUpdated(sub: Stripe.Subscription) {
  // Plan switches (Pro → Studio), trial transitions, pause/resume.
  const customerId = typeof sub.customer === 'string' ? sub.customer : sub.customer.id;
  const plan = planFromSubscription(sub);

  // If the subscription is fully cancelled (already), let the deleted handler
  // do the work — but Stripe will fire customer.subscription.deleted for that.
  if (!plan) {
    console.warn('subscription.updated with no recognised plan', sub.id);
    return;
  }

  // Map stripe status → app-side plan. While Stripe shows 'past_due' or
  // 'unpaid', we keep the user on their plan (Stripe retries automatically).
  // 'canceled' / 'incomplete_expired' fall through to the deleted handler.
  const keepActive = ['active', 'trialing', 'past_due', 'unpaid'];
  if (!keepActive.includes(sub.status)) {
    console.log(`subscription.updated ignored — status=${sub.status}`);
    return;
  }

  const profile = await findProfileByCustomerId(customerId);
  if (!profile) {
    console.warn('subscription.updated for unknown customer', customerId);
    return;
  }

  const update: Record<string, unknown> = {
    plan,
    stripe_subscription_id: sub.id,
  };

  const { error } = await supabase.from('profiles').update(update).eq('id', profile.id);
  if (error) {
    console.error('Profile update failed (subscription.updated)', profile.id, error);
    throw error;
  }
  console.log(`Updated ${profile.id} to plan ${plan} (sub ${sub.id}, status ${sub.status})`);
}

async function handleSubscriptionDeleted(sub: Stripe.Subscription) {
  // Stripe fires this AFTER the billing-period-end if the user cancelled
  // earlier with cancel_at_period_end. The user's access window has now
  // expired — drop them back to free.
  const customerId = typeof sub.customer === 'string' ? sub.customer : sub.customer.id;

  const profile = await findProfileByCustomerId(customerId);
  if (!profile) {
    console.warn('subscription.deleted for unknown customer', customerId);
    return;
  }

  const update: Record<string, unknown> = {
    plan: 'free',
    stripe_subscription_id: null,
    // Keep stripe_customer_id so they can re-subscribe with same card later.
  };

  const { error } = await supabase.from('profiles').update(update).eq('id', profile.id);
  if (error) {
    console.error('Profile update failed (subscription.deleted)', profile.id, error);
    throw error;
  }
  console.log(`Downgraded ${profile.id} to free (sub ${sub.id} ended)`);
}

// ─── HTTP entry point ──────────────────────────────────────────────────────

Deno.serve(async (req: Request) => {
  if (req.method !== 'POST') {
    return new Response('Method not allowed', { status: 405 });
  }

  const sig = req.headers.get('stripe-signature');
  if (!sig) {
    return new Response('Missing stripe-signature header', { status: 400 });
  }

  // We need the raw body bytes to verify the signature. req.text() preserves
  // them as-is.
  const rawBody = await req.text();

  let event: Stripe.Event;
  try {
    // constructEventAsync uses the SubtleCrypto API so it works in Deno
    // without Node's `crypto` module.
    event = await stripe.webhooks.constructEventAsync(
      rawBody,
      sig,
      STRIPE_WEBHOOK_SECRET,
    );
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    console.error('Signature verification failed:', message);
    return new Response(`Bad signature: ${message}`, { status: 400 });
  }

  try {
    switch (event.type) {
      case 'checkout.session.completed':
        await handleCheckoutCompleted(event.data.object as Stripe.Checkout.Session);
        break;
      case 'customer.subscription.updated':
        await handleSubscriptionUpdated(event.data.object as Stripe.Subscription);
        break;
      case 'customer.subscription.deleted':
        await handleSubscriptionDeleted(event.data.object as Stripe.Subscription);
        break;
      case 'invoice.payment_failed':
        // Log only — Stripe automatic dunning handles retries.
        console.warn('invoice.payment_failed', (event.data.object as Stripe.Invoice).id);
        break;
      default:
        // Lots of event types we don't need (invoice.created, customer.created,
        // etc.). Acknowledge so Stripe doesn't retry.
        console.log(`Ignored event type: ${event.type}`);
    }
    return new Response(JSON.stringify({ received: true }), {
      status: 200,
      headers: { 'content-type': 'application/json' },
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    console.error(`Handler failed for ${event.type}:`, message);
    // Returning 500 makes Stripe retry the event with backoff. That's what
    // we want for transient DB errors.
    return new Response(`Handler error: ${message}`, { status: 500 });
  }
});
