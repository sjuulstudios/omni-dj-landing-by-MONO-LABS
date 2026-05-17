"""
Clip Live - Stripe billing integration (Phase 2).

Wraps the Stripe SDK for the two flows the Flask app needs:

  - start_checkout(user_id, email, plan, ...)
      Creates a Stripe Checkout Session for a paid plan upgrade.
      Returns the hosted-checkout URL the frontend should redirect to.

  - open_portal(stripe_customer_id, return_url)
      Creates a Stripe Customer Portal session so a paying user can
      manage their subscription (cancel, swap plan, update card).

  - plan_from_price_id(price_id)
      Helper used by the Supabase Edge Function (and tests) to map a
      Stripe price ID back to our internal plan name. Living here keeps
      the mapping in one place.

Webhook handling does NOT live in this module — it runs in a Supabase
Edge Function (supabase/functions/stripe-webhook/index.ts) so Stripe can
hit a public URL without exposing the local Flask app to the internet.

If env vars are missing or invalid, the SDK is left uninitialised and
billing endpoints will return a clean error. The rest of the app keeps
running.
"""

import os
import logging
from pathlib import Path

log = logging.getLogger('clip-live.billing')

# Load .env from the same folder as this file (idempotent if auth.py
# already loaded it — dotenv only sets keys that aren't already in
# os.environ).
_ENV_PATH = Path(__file__).resolve().parent / '.env'
try:
    from dotenv import load_dotenv
    load_dotenv(_ENV_PATH)
except ImportError:
    log.error('python-dotenv niet geinstalleerd. Run: pip install python-dotenv')

STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', '').strip()
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY', '').strip()
STRIPE_PRICE_ID_PRO = os.getenv('STRIPE_PRICE_ID_PRO', '').strip()
STRIPE_PRICE_ID_STUDIO = os.getenv('STRIPE_PRICE_ID_STUDIO', '').strip()
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', '').strip()

stripe = None
_configured = False

try:
    import stripe as _stripe
    if STRIPE_SECRET_KEY:
        _stripe.api_key = STRIPE_SECRET_KEY
        # Pin API version so a Stripe-side default change doesn't silently
        # alter event payload shapes. Bump deliberately when needed.
        _stripe.api_version = '2024-06-20'
        stripe = _stripe
        _configured = True
        log.info('Stripe SDK geinitialiseerd (test=%s)', STRIPE_SECRET_KEY.startswith('sk_test_'))
    else:
        log.warning('Stripe niet geconfigureerd: STRIPE_SECRET_KEY ontbreekt in .env')
except ImportError:
    log.error('stripe SDK niet geinstalleerd. Run: pip install stripe')


# ─── Plan ↔ price_id mapping ────────────────────────────────────────────────

_PRICE_TO_PLAN = {}
if STRIPE_PRICE_ID_PRO:
    _PRICE_TO_PLAN[STRIPE_PRICE_ID_PRO] = 'pro'
if STRIPE_PRICE_ID_STUDIO:
    _PRICE_TO_PLAN[STRIPE_PRICE_ID_STUDIO] = 'studio'

_PLAN_TO_PRICE = {v: k for k, v in _PRICE_TO_PLAN.items()}


def plan_from_price_id(price_id):
    """Reverse-lookup: which plan does this Stripe price_id belong to?

    Returns 'pro' | 'studio' | None.
    """
    if not price_id:
        return None
    return _PRICE_TO_PLAN.get(price_id)


def price_id_from_plan(plan):
    """Forward lookup: which Stripe price_id should we charge for this plan?

    Returns the price_id string or None if plan is unknown / not paid.
    Free is intentionally not in the mapping — Free users don't checkout.
    """
    if not plan:
        return None
    return _PLAN_TO_PRICE.get(plan.lower())


# ─── Public API ─────────────────────────────────────────────────────────────

def health_check():
    """Report whether Stripe is wired up and price IDs are present.

    Safe to expose via API. Never returns secret keys — only booleans.
    """
    return {
        'ok': _configured,
        'configured': {
            'secret_key': bool(STRIPE_SECRET_KEY),
            'publishable_key': bool(STRIPE_PUBLISHABLE_KEY),
            'price_id_pro': bool(STRIPE_PRICE_ID_PRO),
            'price_id_studio': bool(STRIPE_PRICE_ID_STUDIO),
            'webhook_secret': bool(STRIPE_WEBHOOK_SECRET),
        },
        'test_mode': STRIPE_SECRET_KEY.startswith('sk_test_') if STRIPE_SECRET_KEY else None,
    }


def start_checkout(user_id, email, plan, success_url, cancel_url, stripe_customer_id=None):
    """Create a Stripe Checkout Session for a subscription upgrade.

    Args:
      user_id: Supabase auth user UUID. Stored as client_reference_id +
        metadata.user_id so the webhook can map back to our user.
      email: user's email address (for Stripe receipts + to dedup customer).
      plan: 'pro' or 'studio'.
      success_url: where Stripe redirects after successful payment. May
        contain '{CHECKOUT_SESSION_ID}' which Stripe substitutes for us.
      cancel_url: where Stripe redirects if the user clicks the back link.
      stripe_customer_id: optional. If we already have one (user is
        switching plans), pass it so Stripe uses the same Customer record
        and the user sees their saved payment method.

    Returns:
      {ok: True, url, session_id} on success
      {ok: False, error} on failure
    """
    if not _configured:
        return {'ok': False, 'error': 'Stripe is niet geconfigureerd (zie billing.health_check)'}

    price_id = price_id_from_plan(plan)
    if not price_id:
        return {'ok': False, 'error': f"Onbekend plan '{plan}'. Verwacht 'pro' of 'studio'."}

    try:
        params = {
            'mode': 'subscription',
            'line_items': [{'price': price_id, 'quantity': 1}],
            'client_reference_id': user_id,
            'metadata': {
                'user_id': user_id,
                'plan': plan,
            },
            # Same metadata on the subscription so customer.subscription.*
            # events also know which user/plan we're talking about.
            'subscription_data': {
                'metadata': {
                    'user_id': user_id,
                    'plan': plan,
                },
            },
            'success_url': success_url,
            'cancel_url': cancel_url,
            'allow_promotion_codes': True,
            'billing_address_collection': 'auto',
        }

        if stripe_customer_id:
            # Returning user — reuse existing customer so saved card and
            # tax history carry over.
            params['customer'] = stripe_customer_id
            params['customer_update'] = {'address': 'auto', 'name': 'auto'}
        else:
            # First-time checkout for this user — Stripe will create a new
            # Customer record. customer_email pre-fills the email field
            # and lets Stripe dedup against an existing test customer.
            params['customer_email'] = email
            # Auto-fill VAT for EU customers — Sjuul's terms reference VAT
            # added at checkout based on billing country.
            params['automatic_tax'] = {'enabled': False}  # opt-in later when Stripe Tax is set up

        session = stripe.checkout.Session.create(**params)
        return {
            'ok': True,
            'url': session.url,
            'session_id': session.id,
        }
    except Exception as e:
        log.exception('Stripe checkout creation failed')
        return {'ok': False, 'error': f'{type(e).__name__}: {str(e)}'}


def open_portal(stripe_customer_id, return_url):
    """Create a Stripe Customer Portal session.

    The portal lets the user cancel, swap plan, update card, view invoices,
    etc. — all without us building those screens ourselves.

    Args:
      stripe_customer_id: must come from profiles.stripe_customer_id, set
        by the webhook on first checkout. If empty, return an error
        telling the caller the user has never paid yet.
      return_url: where Stripe sends the user when they click "Return to
        Clip Live".

    Returns:
      {ok: True, url} on success
      {ok: False, error} on failure
    """
    if not _configured:
        return {'ok': False, 'error': 'Stripe is niet geconfigureerd (zie billing.health_check)'}

    if not stripe_customer_id:
        return {'ok': False, 'error': 'Geen Stripe customer gekoppeld aan deze account. Eerst upgraden via Checkout.'}

    try:
        session = stripe.billing_portal.Session.create(
            customer=stripe_customer_id,
            return_url=return_url,
        )
        return {'ok': True, 'url': session.url}
    except Exception as e:
        log.exception('Stripe portal session creation failed')
        return {'ok': False, 'error': f'{type(e).__name__}: {str(e)}'}
