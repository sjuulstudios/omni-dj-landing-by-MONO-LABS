"""
tests/test_mid_analysis_upgrade.py
SESSIE 83 (2026-06-11) - E2E-test voor de mid-analysis upgrade
(laag 2 uit Sectie 4 van PLAN-QUOTA-PAYMENT-HARDENING-2026-06-11.md).

Wat dit bewijst:
  1. reserve-at-start: een geaccepteerde analyse claimt de plek METEEN
     (teller 1 -> 2 zodra de upload geaccepteerd is, niet pas aan het einde).
  2. Een plan-upgrade MIDDEN in de analyse (gesimuleerde Stripe-webhook:
     plan=pro, usage=0, vers window) breekt niets: de analyse maakt af.
  3. Geen eind-increment: na afloop staat de teller nog op 0 (de webhook-
     reset is leidend), dus geen race tussen webhook en jobeinde.
  4. De volgende analyse mag direct onder het nieuwe plan.

Geen echte Stripe of kaart nodig: we voeren exact dezelfde profielmutatie
uit die de webhook doet, via de service_role key uit dezelfde .env als de app.

Vereist:
  - dev-server draait (default http://127.0.0.1:5599, override via OMNI_TEST_BASE)
  - .env naast app.py met SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY
  - migratie 012 toegepast + nieuwe app.py-code actief (herstart na edit!)
  - env-vars:
      OMNI_TEST_EMAIL     testaccount e-mail
      OMNI_TEST_PASSWORD  testaccount wachtwoord
      OMNI_TEST_SET       absoluut pad naar een KORTE testset (mp4/mov)

Run:  bash tests/run_mid_upgrade_test.sh
  of: python3 -m pytest tests/test_mid_analysis_upgrade.py -s
"""

import os
import sys
import time

import httpx

HERE = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.dirname(HERE)
sys.path.insert(0, APP_DIR)

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(APP_DIR, '.env'))
except ImportError:
    pass

BASE = os.environ.get('OMNI_TEST_BASE', 'http://127.0.0.1:5599').rstrip('/')
EMAIL = os.environ.get('OMNI_TEST_EMAIL', '')
PASSWORD = os.environ.get('OMNI_TEST_PASSWORD', '')
TEST_SET = os.environ.get('OMNI_TEST_SET', '')
SUPABASE_URL = os.environ.get('SUPABASE_URL', '').strip()
SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '').strip()
POLL_TIMEOUT_S = int(os.environ.get('OMNI_TEST_TIMEOUT', '1800'))


def _step(msg):
    print(f"\n=== {msg} ===", flush=True)


def _check(label, expected, actual):
    ok = expected == actual
    print(f"  {label}: verwacht={expected!r} werkelijk={actual!r} -> {'OK' if ok else 'FAIL'}",
          flush=True)
    assert ok, f"{label}: verwacht {expected!r}, kreeg {actual!r}"


def _admin():
    from supabase import create_client
    assert SUPABASE_URL and SERVICE_KEY, (
        'SUPABASE_URL/SUPABASE_SERVICE_ROLE_KEY ontbreken (.env naast app.py nodig)')
    return create_client(SUPABASE_URL, SERVICE_KEY)


def _quota(client, token):
    r = client.get(f'{BASE}/api/quota', headers={'Authorization': f'Bearer {token}'})
    r.raise_for_status()
    return r.json()


def test_mid_analysis_upgrade():
    assert EMAIL and PASSWORD, 'Zet OMNI_TEST_EMAIL en OMNI_TEST_PASSWORD'
    assert TEST_SET and os.path.isfile(TEST_SET), (
        f'OMNI_TEST_SET moet naar een bestaand videobestand wijzen (nu: {TEST_SET!r})')

    client = httpx.Client(timeout=60.0)
    admin = _admin()

    _step('1. Login')
    r = client.post(f'{BASE}/api/auth/login', json={'email': EMAIL, 'password': PASSWORD})
    r.raise_for_status()
    token = r.json().get('access_token')
    assert token, f'Geen access_token: {r.text[:200]}'
    user_id = r.json().get('user_id') or r.json().get('user', {}).get('id')
    if not user_id:
        resp = admin.table('profiles').select('id').eq('email', EMAIL).single().execute()
        user_id = resp.data['id']
    print(f'  user_id={user_id}')

    _step('2. Uitgangssituatie: Free, used=1, vers window (gesimuleerd)')
    admin.table('profiles').update({
        'plan': 'free',
        'usage_this_period': 1,
        'quota_reset_date': '2099-01-01T00:00:00Z',
    }).eq('id', user_id).execute()
    # Window ver in de toekomst zodat een window-roll de test niet vervuilt;
    # de webhook-simulatie zet straks een realistisch window.
    q = _quota(client, token)
    _check('plan', 'free', q['plan'])
    _check('used', 1, q['used'])
    _check('limit', 2, q['limit'])

    _step('3. Start analyse 2 van 2 (reserve-at-start claimt de plek direct)')
    r = client.post(f'{BASE}/api/upload-local',
                    headers={'Authorization': f'Bearer {token}'},
                    json={'path': TEST_SET})
    print(f'  HTTP {r.status_code}: {r.text[:200]}')
    assert r.status_code == 200, f'upload-local faalde: {r.status_code} {r.text[:300]}'
    job_id = r.json()['job_id']
    print(f'  job_id={job_id}')

    q = _quota(client, token)
    _check('used direct na accept (reserve-at-start)', 2, q['used'])

    resv = admin.table('quota_reservations').select('state').eq('job_id', job_id) \
                .single().execute().data
    _check('reservering state', 'reserved', resv['state'])

    _step('4. Webhook-simulatie MIDDEN in de analyse: upgrade naar Pro')
    # Exact dezelfde mutatie als handleCheckoutCompleted in stripe-webhook.
    from datetime import datetime, timedelta, timezone
    new_reset = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    admin.table('profiles').update({
        'plan': 'pro',
        'usage_this_period': 0,
        'quota_reset_date': new_reset,
    }).eq('id', user_id).execute()
    print('  profiel: plan=pro, usage=0, vers window gezet')

    _step('5. Wachten tot de analyse klaar is (mag NIET breken door de upgrade)')
    t0 = time.time()
    status = None
    while time.time() - t0 < POLL_TIMEOUT_S:
        s = client.get(f'{BASE}/api/status/{job_id}',
                       headers={'Authorization': f'Bearer {token}'})
        if s.status_code == 200:
            status = s.json().get('status')
            if status in ('done', 'error'):
                break
        time.sleep(5)
    print(f'  eindstatus na {int(time.time() - t0)}s: {status}')
    _check('analyse-eindstatus', 'done', status)

    _step('6. Geen eind-increment: teller blijft op de webhook-reset staan')
    q = _quota(client, token)
    _check('plan na upgrade', 'pro', q['plan'])
    _check('used na afloop (geen dubbeltelling)', 0, q['used'])
    _check('limit onder pro', 10, q['limit'])

    resv = admin.table('quota_reservations').select('state').eq('job_id', job_id) \
                .single().execute().data
    # 'finalised' bij clips; 'released' als de testset 0 drops opleverde
    # (lege set geeft de plek terug, ook correct). Beide zijn terminaal.
    print(f"  reservering eindstate: {resv['state']}")
    assert resv['state'] in ('finalised', 'released'), resv

    _step('7. Volgende analyse mag direct onder Pro')
    _check('remaining > 0', True, (q['remaining'] is None) or (q['remaining'] > 0))

    print('\nALLE E2E-CHECKS GROEN: upgrade mid-analyse is correct afgehandeld.')


if __name__ == '__main__':
    test_mid_analysis_upgrade()
