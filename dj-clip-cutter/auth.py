"""
Clip Live - Authentication & Supabase integration.

Loads SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY from .env
and exposes two clients:

  - supabase_client: anon-key client for user-facing flows (signup, login,
    user-scoped reads). Subject to Row Level Security.
  - supabase_admin: service_role client for server-side operations like
    Stripe webhook plan-updates. Bypasses RLS.

If env vars are missing or invalid, the corresponding client is None and
the rest of the app continues to run. Auth-protected routes will refuse
service until config is fixed; non-auth routes (existing tool features)
remain fully functional.
"""

import os
import logging
from pathlib import Path

log = logging.getLogger('clip-live.auth')

# Load .env from the same folder as this file
_ENV_PATH = Path(__file__).resolve().parent / '.env'
try:
    from dotenv import load_dotenv
    load_dotenv(_ENV_PATH)
except ImportError:
    log.error('python-dotenv niet geinstalleerd. Run: pip install python-dotenv')

SUPABASE_URL = os.getenv('SUPABASE_URL', '').strip()
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY', '').strip()
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '').strip()

supabase_client = None
supabase_admin = None

try:
    from supabase import create_client

    if SUPABASE_URL and SUPABASE_ANON_KEY:
        try:
            supabase_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
            log.info('Supabase anon client geinitialiseerd')
        except Exception as e:
            log.error(f'Supabase anon client init failed: {e}')
    else:
        log.warning('Supabase niet geconfigureerd: SUPABASE_URL of SUPABASE_ANON_KEY ontbreekt in .env')

    if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
        try:
            supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
            log.info('Supabase admin client geinitialiseerd')
        except Exception as e:
            log.error(f'Supabase admin client init failed: {e}')
    else:
        log.warning('Supabase service_role niet geconfigureerd - webhooks werken nog niet')

except ImportError:
    log.error('supabase-py niet geinstalleerd. Run: pip install supabase')


def health_check():
    """Verify Supabase connection by attempting a small read.
    Returns dict with ok/error fields, safe to expose via API.
    Never returns secret keys - only whether they're configured."""
    if supabase_client is None:
        return {
            'ok': False,
            'error': 'Supabase client niet geconfigureerd. Check .env.',
            'configured': {
                'url': bool(SUPABASE_URL),
                'anon_key': bool(SUPABASE_ANON_KEY),
                'service_role_key': bool(SUPABASE_SERVICE_ROLE_KEY),
            },
        }

    try:
        # Anon-key call: returns rows visible per RLS (zero for unauthenticated).
        # The call itself succeeds only if URL + key + network are all valid.
        result = supabase_client.table('profiles').select('id', count='exact').limit(1).execute()
        count = getattr(result, 'count', None)
        return {
            'ok': True,
            'supabase_url': SUPABASE_URL,
            'profiles_visible_to_anon': count if count is not None else 0,
            'admin_client_configured': supabase_admin is not None,
        }
    except Exception as e:
        return {
            'ok': False,
            'error': f'{type(e).__name__}: {str(e)}',
            'supabase_url': SUPABASE_URL,
        }


def signup(email, password, intake=None):
    """Register a new user via Supabase auth. The handle_new_user trigger
    will auto-create their profiles row with plan='free' + 30-day quota window.

    SESSIE 22 — `intake` (optional dict) captures the pre-signup questionnaire
    answers. After a successful sign_up we patch the profiles row with the
    intake fields via the service_role client (bypasses RLS). Intake schema:

      {
        referral_source: str,         # friend / manager / whatsapp / ... / other
        referral_other:  str|None,    # filled iff referral_source == 'other'
        use_reasons:     list[str],   # 1..4 slugs
        artist_name:     str,         # required
        full_name:       str,         # required
        instagram_url:   str|None,
        tiktok_url:      str|None,
        streaming_url:   str|None,
      }

    Returns:
      {ok: True, access_token, refresh_token, expires_at, user_id, email}
        if signup succeeded and session was issued (email confirmation OFF)
      {ok: True, requires_email_confirmation: True, user_id, email}
        if signup succeeded but Supabase requires email confirmation first
      {ok: False, error: '...'}
        on any failure
    """
    if supabase_client is None:
        return {'ok': False, 'error': 'Supabase client niet geconfigureerd'}
    try:
        result = supabase_client.auth.sign_up({
            'email': email,
            'password': password,
        })
        if result is None or result.user is None:
            return {'ok': False, 'error': 'Signup geweigerd door Supabase'}

        # Persist intake answers via service_role (the new profiles row was
        # just inserted by the on_auth_user_created trigger). Soft-fail: if
        # the update errors we still return success — the user exists and can
        # log in; intake just won't be recorded.
        if intake and supabase_admin is not None and result.user is not None:
            try:
                _persist_intake(result.user.id, intake)
            except Exception as e:
                log.warning(f'Intake persist failed for user {result.user.id}: {e}')

        if result.session is None:
            # Email confirmation flow active in Supabase project
            return {
                'ok': True,
                'requires_email_confirmation': True,
                'user_id': result.user.id,
                'email': email,
            }
        return {
            'ok': True,
            'access_token': result.session.access_token,
            'refresh_token': result.session.refresh_token,
            'expires_at': result.session.expires_at,
            'user_id': result.user.id,
            'email': result.user.email,
        }
    except Exception as e:
        return {'ok': False, 'error': f'{type(e).__name__}: {str(e)}'}


def _persist_intake(user_id, intake):
    """Upsert the signup-questionnaire answers onto the profiles row.
    Called from signup() AFTER auth.sign_up succeeds. Safe to call repeatedly
    (idempotent). Whitelists allowed columns so a rogue client can't sneak in
    extra fields via the JSON body."""
    import datetime
    allowed_referral = {'friend','manager','whatsapp','tiktok','instagram','google','reddit','facebook','other'}
    allowed_reasons  = {'cant_afford_videographer','saves_time','easier_sharing','share_right_after_show'}
    payload = {}

    rs = (intake or {}).get('referral_source')
    if isinstance(rs, str) and rs.lower() in allowed_referral:
        payload['referral_source'] = rs.lower()
    ro = (intake or {}).get('referral_other')
    if isinstance(ro, str) and ro.strip():
        payload['referral_other'] = ro.strip()[:240]
    ur = (intake or {}).get('use_reasons')
    if isinstance(ur, list):
        payload['use_reasons'] = [r for r in ur if isinstance(r, str) and r in allowed_reasons]
    for k_in, k_out, max_len in [
        ('artist_name',   'artist_name',   80),
        ('full_name',     'full_name',     120),
        ('instagram_url', 'instagram_url', 240),
        ('tiktok_url',    'tiktok_url',    240),
        ('streaming_url', 'streaming_url', 240),
    ]:
        v = (intake or {}).get(k_in)
        if isinstance(v, str) and v.strip():
            payload[k_out] = v.strip()[:max_len]
    if not payload:
        return
    payload['intake_completed_at'] = datetime.datetime.utcnow().isoformat() + 'Z'
    supabase_admin.table('profiles').update(payload).eq('id', user_id).execute()


def login(email, password):
    """Sign in existing user with email + password.

    Returns:
      {ok: True, access_token, refresh_token, expires_at, user_id, email}
        on success
      {ok: False, error: '...'}
        on bad credentials or other failure
    """
    if supabase_client is None:
        return {'ok': False, 'error': 'Supabase client niet geconfigureerd'}
    try:
        result = supabase_client.auth.sign_in_with_password({
            'email': email,
            'password': password,
        })
        if result is None or result.session is None or result.user is None:
            return {'ok': False, 'error': 'Login mislukt'}
        return {
            'ok': True,
            'access_token': result.session.access_token,
            'refresh_token': result.session.refresh_token,
            'expires_at': result.session.expires_at,
            'user_id': result.user.id,
            'email': result.user.email,
        }
    except Exception as e:
        return {'ok': False, 'error': f'{type(e).__name__}: {str(e)}'}


def get_user_from_token(access_token):
    """Verify a JWT and return user info + their profiles row.

    Validates the token with Supabase's auth service, then fetches the
    user's profile (plan, usage, quota_reset_date) via the admin client.

    Returns dict with user/profile info or None if token invalid.
    """
    if supabase_client is None or not access_token:
        return None
    try:
        user_resp = supabase_client.auth.get_user(access_token)
        if not user_resp or not getattr(user_resp, 'user', None):
            return None
        user = user_resp.user
        profile = None
        if supabase_admin is not None:
            try:
                prof_resp = supabase_admin.table('profiles').select('*').eq('id', user.id).single().execute()
                profile = getattr(prof_resp, 'data', None)
            except Exception as e:
                log.warning(f'Profile fetch failed for user {user.id}: {e}')
        return {
            'user_id': user.id,
            'email': user.email,
            'profile': profile,
        }
    except Exception as e:
        log.warning(f'Token validation failed: {e}')
        return None
