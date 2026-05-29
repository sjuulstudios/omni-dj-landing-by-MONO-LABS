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

# Edge function base URL — gebruikt voor productie/bundle waar
# STRIPE_SECRET_KEY *niet* lokaal beschikbaar is. Default is afgeleid van
# SUPABASE_URL zodat runtime_config (in de bundle) alleen SUPABASE_URL
# hoeft te zetten. In dev kan dotenv 'm overrulen.
_DEFAULT_EDGE_BASE = ''
_supabase_url = os.getenv('SUPABASE_URL', '').strip()
if _supabase_url:
    _DEFAULT_EDGE_BASE = _supabase_url.rstrip('/') + '/functions/v1'
EDGE_FUNCTIONS_BASE_URL = os.getenv('EDGE_FUNCTIONS_BASE_URL', _DEFAULT_EDGE_BASE).strip()

stripe = None
_configured = False
_USE_EDGE_FUNCTIONS = False

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
        # Geen lokale STRIPE_SECRET_KEY — dat is de NORMALE situatie in de
        # gedistribueerde .app/.exe. Checkout en portal vallen terug op de
        # Supabase Edge Functions zolang we EDGE_FUNCTIONS_BASE_URL hebben.
        if EDGE_FUNCTIONS_BASE_URL:
            _USE_EDGE_FUNCTIONS = True
            _configured = True
            log.info('Stripe SDK niet lokaal beschikbaar — checkout/portal via edge functions op %s',
                     EDGE_FUNCTIONS_BASE_URL)
        else:
            log.warning('Stripe niet geconfigureerd: geen STRIPE_SECRET_KEY en geen EDGE_FUNCTIONS_BASE_URL')
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
        'mode': 'edge_functions' if _USE_EDGE_FUNCTIONS else ('local_sdk' if STRIPE_SECRET_KEY else 'unconfigured'),
        'configured': {
            'secret_key': bool(STRIPE_SECRET_KEY),
            'publishable_key': bool(STRIPE_PUBLISHABLE_KEY),
            'price_id_pro': bool(STRIPE_PRICE_ID_PRO),
            'price_id_studio': bool(STRIPE_PRICE_ID_STUDIO),
            'webhook_secret': bool(STRIPE_WEBHOOK_SECRET),
            'edge_functions_base_url': bool(EDGE_FUNCTIONS_BASE_URL),
        },
        'test_mode': (
            STRIPE_PUBLISHABLE_KEY.startswith('pk_test_') if STRIPE_PUBLISHABLE_KEY else None
        ),
    }


def _call_edge_function(name, access_token, body):
    """POST naar een Supabase Edge Function met de Supabase JWT van de user.

    Retourneert dezelfde shape als de directe Stripe-flow:
      {ok: True, url, session_id?} bij succes
      {ok: False, error}            bij elke fout

    Vereist dat 'requests' beschikbaar is (zit al in requirements.txt voor
    de uploader-flow). Timeouts kort houden — Stripe checkout-creatie is
    normaal < 1s.
    """
    if not EDGE_FUNCTIONS_BASE_URL:
        return {'ok': False, 'error': 'EDGE_FUNCTIONS_BASE_URL niet ingesteld'}
    if not access_token:
        return {'ok': False, 'error': 'Edge function vereist een access_token van de ingelogde user'}

    url = f"{EDGE_FUNCTIONS_BASE_URL.rstrip('/')}/{name}"
    try:
        import requests
    except ImportError:
        return {'ok': False, 'error': "requests niet geinstalleerd (pip install requests)"}

    try:
        resp = requests.post(
            url,
            json=body,
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
                # Supabase Edge Functions vereisen de 'apikey' header (anon key)
                # zodra je de function NIET met --no-verify-jwt deployt. We
                # gebruiken de anon key uit env zodat de runtime_config 'm
                # heeft kunnen zetten.
                'apikey': os.getenv('SUPABASE_ANON_KEY', ''),
            },
            timeout=15,
        )
    except Exception as e:
        log.exception('Edge function POST mislukt')
        return {'ok': False, 'error': f'Netwerkfout bij edge function: {e}'}

    if resp.status_code >= 400:
        try:
            data = resp.json()
            err = data.get('error') or resp.text
        except Exception:
            err = resp.text or f'HTTP {resp.status_code}'
        return {'ok': False, 'error': f'Edge function {name}: {err}'}

    try:
        return resp.json()
    except Exception as e:
        return {'ok': False, 'error': f'Onverwacht antwoord van edge function: {e}'}


def start_checkout(user_id, email, plan, success_url, cancel_url,
                   stripe_customer_id=None, access_token=None):
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
      access_token: Supabase JWT van de ingelogde user. Vereist wanneer we
        in edge-function-modus draaien (gebundelde .app). In dev met
        lokale STRIPE_SECRET_KEY wordt deze parameter genegeerd.

    Returns:
      {ok: True, url, session_id} on success
      {ok: False, error} on failure
    """
    if not _configured:
        return {'ok': False, 'error': 'Stripe is niet geconfigureerd (zie billing.health_check)'}

    # ── Edge function pad (geen lokale secret beschikbaar) ────────────── #
    if _USE_EDGE_FUNCTIONS:
        return _call_edge_function(
            'create-checkout-session',
            access_token=access_token,
            body={
                'plan': plan,
                'success_url': success_url,
                'cancel_url': cancel_url,
            },
        )

    # ── Lokaal SDK-pad (dev met .env) ─────────────────────────────────── #
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


def open_portal(stripe_customer_id, return_url, access_token=None):
    """Create a Stripe Customer Portal session.

    The portal lets the user cancel, swap plan, update card, view invoices,
    etc. — all without us building those screens ourselves.

    Args:
      stripe_customer_id: must come from profiles.stripe_customer_id, set
        by the webhook on first checkout. If empty, return an error
        telling the caller the user has never paid yet.
      return_url: where Stripe sends the user when they click "Return to
        Clip Live".
      access_token: Supabase JWT — vereist in edge-function-modus.

    Returns:
      {ok: True, url} on success
      {ok: False, error} on failure
    """
    if not _configured:
        return {'ok': False, 'error': 'Stripe is niet geconfigureerd (zie billing.health_check)'}

    # ── Edge function pad ─────────────────────────────────────────────── #
    if _USE_EDGE_FUNCTIONS:
        return _call_edge_function(
            'create-portal-session',
            access_token=access_token,
            body={'return_url': return_url},
        )

    # ── Lokaal SDK-pad ────────────────────────────────────────────────── #
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
