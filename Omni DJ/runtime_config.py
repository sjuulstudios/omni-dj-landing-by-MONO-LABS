"""
Clip Live — runtime configuration

Hardcoded publieke configuratiewaarden die nodig zijn om de gebundelde
desktop-app te laten werken zonder een .env-bestand naast de bundel.

Deze waarden worden alleen ingevuld als ze nog niet in os.environ staan.
In een dev-setup overrulet je .env dus altijd deze defaults — geen
gedragsverandering bij lokaal ontwikkelen.

WAT MAG HIER STAAN
------------------
- SUPABASE_URL                 — projecturl, publiek
- SUPABASE_ANON_KEY            — anon JWT, expliciet veilig voor frontends
                                 (Row Level Security beschermt data)
- STRIPE_PUBLISHABLE_KEY       — pk_test_… of pk_live_…, expliciet publiek
- STRIPE_PRICE_ID_PRO/STUDIO   — Stripe price IDs, publiek (geen credentials)
- EDGE_FUNCTIONS_BASE_URL      — basis-URL van Supabase Edge Functions,
                                 gewoon publiek

WAT MAG HIER NIET STAAN
-----------------------
- SUPABASE_SERVICE_ROLE_KEY    — bypass RLS. Hoort alleen als Supabase
                                 secret voor edge functions (`supabase
                                 secrets set ...`).
- STRIPE_SECRET_KEY            — kan willekeurige Stripe-API calls doen.
                                 Hoort alleen als Supabase secret.
- STRIPE_WEBHOOK_SECRET        — verifieert webhook signatures. Idem.

Bij elke nieuwe release: bump VERSION + update keys als je environment
verandert (LIVE-mode, andere prijzen, andere Supabase project).
"""

import os

VERSION = "0.1.0-beta"

# ------------------------------------------------------------------ #
# Hardcoded publieke waarden — vervang bij overgang naar Stripe LIVE.
# ------------------------------------------------------------------ #
_DEFAULTS = {
    "SUPABASE_URL": "https://lbabsffxefkrxwzkbzar.supabase.co",
    "SUPABASE_ANON_KEY": (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxiYWJzZmZ4ZWZrcnh3emtiemFyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzgwODEyNDksImV4cCI6MjA5MzY1NzI0OX0."
        "4_T3oIvMLdGRtpZXISNbEub1V0LVISNDwXe8DZHSaS0"
    ),
    # TEST-mode Stripe — voor beta. Vervang door pk_live_… voor publieke launch.
    "STRIPE_PUBLISHABLE_KEY": (
        "pk_test_51S9RckA5DKhJaSAFc5s3eWFINEuC7ye8yqfZxiC18rEZZCuWmXGYh4xYP1qM2Z28eCxqJgAPIxkONoRWOQc6zUTx00ErzgBlRm"
    ),
    "STRIPE_PRICE_ID_PRO": "price_1TUoYNA5DKhJaSAF6xynooY9",
    "STRIPE_PRICE_ID_STUDIO": "price_1TUoZCA5DKhJaSAFI7AMgAbA",
    # Basis-URL voor edge functions = SUPABASE_URL + /functions/v1
    # billing.py voegt zelf de function-naam toe.
    "EDGE_FUNCTIONS_BASE_URL": "https://lbabsffxefkrxwzkbzar.supabase.co/functions/v1",
}


def apply_defaults() -> None:
    """Zet de hardcoded waarden in os.environ, alleen als ze er nog niet
    staan. Wordt geroepen door launcher.py voordat app.py / auth.py /
    billing.py worden geïmporteerd, zodat dotenv (indien aanwezig) nog
    steeds kan overrulen door zelf hogere prioriteit te krijgen — maar
    in de gebundelde .app waar geen .env meekomt, vallen we op deze
    defaults terug."""
    for key, value in _DEFAULTS.items():
        if not os.environ.get(key):
            os.environ[key] = value
