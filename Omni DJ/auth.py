"""
Omni DJ - Authentication & Supabase integration.

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


def call_update_usage_edge_function(access_token, action, job_id=None):
    """SESSIE 30 - Call the `update-usage` edge function with the user's JWT
    for server-side quota bookkeeping. Used by the bundled .app where
    SUPABASE_SERVICE_ROLE_KEY is intentionally absent.

    action: 'get' | 'reserve' | 'release' | 'finalize' | 'increment'
    SESSIE 83 - reserve/release/finalize vereisen een job_id (atomaire
    quota-RPC's uit migratie 012); 'increment' blijft als compat-alias.
    Returns the parsed JSON response dict on success, or {'ok': False, 'error': ...}.
    """
    if not SUPABASE_URL or not access_token:
        return {'ok': False, 'error': 'Supabase URL of access_token ontbreekt'}
    try:
        import httpx
        url = SUPABASE_URL.rstrip('/') + '/functions/v1/update-usage'
        headers = {
            'Authorization': f'Bearer {access_token}',
            'apikey': SUPABASE_ANON_KEY,
            'Content-Type': 'application/json',
        }
        payload = {'action': action}
        if job_id is not None:
            payload['job_id'] = str(job_id)
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(url, headers=headers, json=payload)
        if resp.status_code >= 400:
            try:
                body = resp.json()
                err = body.get('error') or resp.text
            except Exception:
                err = resp.text
            return {'ok': False, 'error': f'edge function {resp.status_code}: {err}'}
        return resp.json()
    except Exception as e:
        return {'ok': False, 'error': f'{type(e).__name__}: {e}'}


def refresh_session(refresh_token):
    """SESSIE 30b - exchange a refresh_token for a new access_token + a
    rotated refresh_token. Used by /api/auth/refresh so the desktop app
    can keep going indefinitely without forcing users to log in each
    hour.

    Returns:
      {ok: True, access_token, refresh_token, expires_at, user_id, email}
      {ok: False, error: '...'}
    """
    if supabase_client is None:
        return {'ok': False, 'error': 'Supabase client niet geconfigureerd'}
    if not refresh_token:
        return {'ok': False, 'error': 'refresh_token ontbreekt'}
    try:
        # supabase-py 2.x exposes refresh_session via set_session(...) or
        # explicitly via the auth API. Use set_session which is the public,
        # documented path - it takes (access_token, refresh_token), rotates
        # them, and returns a fresh Session.
        result = supabase_client.auth.refresh_session(refresh_token)
        if result is None or result.session is None or result.user is None:
            return {'ok': False, 'error': 'Refresh geweigerd door Supabase'}
        return {
            'ok': True,
            'access_token':  result.session.access_token,
            'refresh_token': result.session.refresh_token,
            'expires_at':    result.session.expires_at,
            'user_id':       result.user.id,
            'email':         result.user.email,
        }
    except Exception as e:
        return {'ok': False, 'error': f'{type(e).__name__}: {str(e)}'}


def get_user_role(user_id):
    """SESSIE 35 — Haal de role op voor een user_id uit de profiles tabel.
    Gebruikt supabase_admin (service_role) voor een betrouwbare, RLS-vrije read.

    Returns:
        'user' | 'beta' | 'admin'  — altijd een geldige string, default 'user'
        None als supabase_admin niet geconfigureerd is of de query faalt.
    """
    if supabase_admin is None or not user_id:
        return None
    try:
        resp = supabase_admin.table('profiles').select('role').eq('id', user_id).single().execute()
        data = getattr(resp, 'data', None) or {}
        return data.get('role') or 'user'
    except Exception as e:
        log.warning('get_user_role failed for %s: %s', user_id, e)
        return None


def require_role(role):
    """SESSIE 35 — Flask route decorator die een minimale rol vereist.

    Gebruik:
        @app.route('/api/admin/something')
        @require_role('admin')
        def admin_endpoint():
            ...

    De decorator verwacht dat het actieve Flask-request een geldig Bearer token
    heeft (Authorization: Bearer <jwt>). Als de user niet ingelogd is, of de rol
    niet voldoende is, wordt 401 of 403 teruggegeven.

    Args:
        role: vereiste minimale rol. Hiërarchie: user < beta < admin.
              Bij role='admin' wordt alleen 'admin' toegelaten.
              Bij role='beta' worden 'beta' en 'admin' toegelaten.
              Bij role='user' worden alle ingelogde users toegelaten.
    """
    import functools
    from flask import request, jsonify

    ROLE_HIERARCHY = {'user': 0, 'beta': 1, 'admin': 2}
    required_level = ROLE_HIERARCHY.get(role, 99)

    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get('Authorization', '')
            if not auth_header.lower().startswith('bearer '):
                return jsonify({'ok': False, 'error': 'Geen Authorization header'}), 401
            token = auth_header[7:].strip()
            user_info = get_user_from_token(token)
            if not user_info:
                return jsonify({'ok': False, 'error': 'Ongeldig of verlopen token'}), 401
            user_role = get_user_role(user_info['user_id']) or 'user'
            user_level = ROLE_HIERARCHY.get(user_role, 0)
            if user_level < required_level:
                log.warning(
                    'require_role(%s) geblokkeerd: user %s heeft role=%s',
                    role, user_info['user_id'], user_role,
                )
                return jsonify({
                    'ok': False,
                    'error': f'Toegang geweigerd. Vereiste rol: {role}, jouw rol: {user_role}.',
                }), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator


def log_action(action, user_id=None, ip_address=None, user_agent=None, metadata=None):
    """SESSIE 35 — Schrijf een immutable audit-log-regel naar Supabase.

    Gebruikt supabase_admin (service_role) zodat RLS nooit in de weg zit.
    Fire-and-forget: fouten worden gelogd maar nooit geraised — een trage
    of tijdelijk neergegane Supabase mag nooit een gebruikersverzoek blokkeren.

    Args:
        action      : vaste string, bv. "auth.login", "clip.export", "plan.upgrade"
        user_id     : UUID string van de ingelogde user, of None bij mislukte login
        ip_address  : IPv4/IPv6 string van de client
        user_agent  : browser/app user-agent string
        metadata    : dict met extra context, bv. {"plan": "studio"}
    """
    if supabase_admin is None:
        # Admin client niet geconfigureerd (bundled .app zonder service_role key).
        # Stil skippen — niet loggen is beter dan de aanroeper te crashen.
        return
    try:
        row = {
            'action': action,
            'user_id': user_id,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'metadata': metadata or {},
        }
        supabase_admin.table('audit_logs').insert(row).execute()
    except Exception as e:
        # Nooit re-raisen. Audit log is best-effort.
        log.warning('audit log schrijven mislukt (action=%s user=%s): %s', action, user_id, e)


# ---------------------------------------------------------------------------
# SESSIE 40 (2026-05-26) — Password Reset Flow
# ---------------------------------------------------------------------------
# Volgt SESSIE34-PASSWORD-RESET-PLAN.md. Leunt op Supabase Auth voor token
# generatie/expiry/one-time-use. Wij doen alleen email/password validatie en
# rate-limiting (rate-limit zit op endpoint-niveau in app.py).
#
# Belangrijk: forgot_password() MOET altijd hetzelfde returnen ongeacht of
# het email bestaat — anders is account-enumeration mogelijk.
# ---------------------------------------------------------------------------

import re

_EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')

# Common-password blacklist — uitbreiden post-launch op basis van logs.
_COMMON_PASSWORDS = {
    'password', 'password1', 'password123', '12345678', '123456789',
    'qwerty123', 'qwerty1234', 'letmein1', 'letmein123',
    'welcome1', 'welcome123', 'admin123', 'administrator',
    'omnidj1', 'omnidj123', 'omni1', 'omni123',
    'iloveyou1', 'monkey123', 'dragon123', 'football1',
}


def _is_valid_email(email):
    """Basic email-format check. Lengte-cap voorkomt log-spam DoS via 10MB strings."""
    return bool(email) and len(email) <= 254 and bool(_EMAIL_RE.match(email))


def _is_strong_password(pw):
    """NIST-conform: lengte + blacklist + minimaal letter + cijfer-of-symbool.
    Geen verplichte hoofdletter/symbool — onderzoek toont dat dat 'Welkom1!'
    patronen oplevert die zwakker zijn dan een lange passphrase."""
    if not pw or not isinstance(pw, str):
        return False
    if len(pw) < 8 or len(pw) > 128:
        return False
    if pw.lower() in _COMMON_PASSWORDS:
        return False
    has_letter = any(c.isalpha() for c in pw)
    has_digit_or_sym = any(not c.isalpha() for c in pw)
    return has_letter and has_digit_or_sym


def _reset_redirect_url():
    """Waar Supabase de gebruiker heen stuurt na klik op reset-link.
    Lokaal (dev-server + .app) is dat 127.0.0.1:5555. Productie is omnidj.com.
    Beide URLs MOETEN in de Supabase URL-allowlist staan, anders weigert
    Supabase de redirect (security-feature, geen bug)."""
    return os.getenv(
        'RESET_REDIRECT_URL',
        'http://127.0.0.1:5555/static/reset-password.html',
    )


def forgot_password(email):
    """Trigger Supabase om een reset-link te mailen naar `email`.

    SECURITY: deze functie MOET altijd dezelfde response returnen — ongeacht
    of het emailadres bestaat, ongeacht of Supabase tijdelijk down is. Anders
    kan een aanvaller via response-verschillen ontdekken welke emails in onze
    database staan (account-enumeration).

    Rate-limiting zit op endpoint-niveau in app.py (per-IP + per-email).
    """
    if supabase_client is None:
        return {'ok': True}  # config-error mag óók niet lekken

    if not _is_valid_email(email):
        return {'ok': True}  # silent reject — ziet er hetzelfde uit als success

    try:
        supabase_client.auth.reset_password_email(
            email,
            options={'redirect_to': _reset_redirect_url()},
        )
    except Exception as e:
        # Log, maar lek niet naar de caller
        log.warning('reset_password_email failed for %s: %s', email, e)

    return {'ok': True}


def reset_password(access_token, refresh_token, new_password):
    """Pas een nieuw wachtwoord toe nadat gebruiker op de reset-link klikte.

    Supabase's flow: de mail-link plaatst access_token + refresh_token in de
    URL-fragment (#access_token=...&refresh_token=...&type=recovery). De
    frontend extraheert die, stuurt ze samen met het nieuwe wachtwoord
    hierheen, en wij gebruiken ze om een tijdelijke session op te zetten
    waarmee we het password kunnen updaten.

    Wat we DAARNA doen: alle andere sessies van die user invalideren via
    de admin API. Zo kan een aanvaller die het account al gehijackt had
    er nu uitgegooid worden.
    """
    if supabase_client is None:
        return {'ok': False, 'error': 'Auth niet beschikbaar'}

    if not access_token or not refresh_token:
        return {'ok': False, 'error': 'Reset-link ongeldig of verlopen'}

    if not _is_strong_password(new_password):
        return {
            'ok': False,
            'error': 'Wachtwoord moet 8-128 tekens zijn, minstens 1 letter en 1 cijfer of symbool, en geen veelgebruikt wachtwoord.',
        }

    try:
        # Zet een sessie op vanuit de recovery-tokens. In supabase-py 2.30+
        # returnt set_session() een AuthResponse met .user EN .session attrs.
        sess = supabase_client.auth.set_session(access_token, refresh_token)
        if not sess or not getattr(sess, 'user', None):
            return {'ok': False, 'error': 'Reset-link ongeldig of verlopen'}

        # Update password terwijl we als die user geauthenticeerd zijn.
        # update_user() returnt UserResponse — heeft .user maar GEEN .session.
        result = supabase_client.auth.update_user({'password': new_password})
        if not result or not getattr(result, 'user', None):
            return {'ok': False, 'error': 'Update mislukt'}

        # Hardening: probeer alle andere sessies te invalideren. Als dit faalt
        # (verschillende supabase-py versies hebben andere admin.sign_out
        # signatures, of admin client is niet geconfigureerd in bundled .app),
        # is dat NIET fataal — password is al gewijzigd. We loggen en gaan
        # door, want de gebruiker krijgt anders een onnodige error.
        # TODO sessie 41: signature correct krijgen of via REST call doen.
        if supabase_admin is not None:
            try:
                # supabase-py 2.30 verwacht een Session-object of jwt-string,
                # niet user_id. Probeer beide vormen.
                try:
                    supabase_admin.auth.admin.sign_out(access_token)
                except TypeError:
                    supabase_admin.auth.admin.sign_out(result.user.id)
            except Exception as e:
                log.warning('sign_out other sessions failed for %s: %s', result.user.id, e)

        # De tokens uit set_session zijn nog steeds geldig — Supabase
        # invalideert ze pas bij expliciete logout of expiry. Plus: sess
        # is een AuthResponse met .session.access_token en .session.refresh_token.
        # Veilig pad: pak ze daaruit, val terug op de input-tokens als de
        # response-shape onverwacht is.
        sess_obj = getattr(sess, 'session', None)
        out_access  = getattr(sess_obj, 'access_token',  None) if sess_obj else None
        out_refresh = getattr(sess_obj, 'refresh_token', None) if sess_obj else None
        if not out_access:  out_access  = access_token
        if not out_refresh: out_refresh = refresh_token

        return {
            'ok': True,
            'access_token':  out_access,
            'refresh_token': out_refresh,
            'user_id':       result.user.id,
            'email':         result.user.email,
        }
    except Exception as e:
        log.warning('reset_password failed: %s', e)
        return {'ok': False, 'error': 'Reset mislukt — vraag een nieuwe link aan'}


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
        else:
            # SESSIE 30 - bundled .app fallback: fetch profile via edge function
            # using the caller's own JWT. Never raises, only logs.
            try:
                edge_resp = call_update_usage_edge_function(access_token, 'get')
                if edge_resp.get('ok'):
                    profile = edge_resp.get('profile')
                else:
                    log.warning(
                        'Profile fetch via edge function failed for user %s: %s',
                        user.id, edge_resp.get('error'),
                    )
            except Exception as e:
                log.warning(f'Profile fetch via edge function raised for {user.id}: {e}')
        return {
            'user_id': user.id,
            'email': user.email,
            'profile': profile,
        }
    except Exception as e:
        log.warning(f'Token validation failed: {e}')
        return None
