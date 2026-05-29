# SESSIE 34 — Password Reset Flow Plan

> Datum: 2026-05-24
> Status: Plan-document — niets geïmplementeerd
> Author: Claude (sessie 34) op verzoek van Sjuul, vooruitlopend op de eerste echte beta-gebruikers
> Voorrang: hoger dan caption-fonts plan want dit is een security-critical user flow die ontbreekt vóór launch

---

## Waarom dit plan-doc bestaat

`auth.py` heeft `signup`, `login`, `refresh_session`, `get_user_from_token` — maar **geen password reset endpoint, geen forgot-password UI, geen email template**. Zodra de eerste beta-gebruiker zijn wachtwoord vergeet, kan hij niet meer in zijn account, en is jouw enige optie als operator: handmatig met Supabase admin een password te wijzigen. Onhoudbaar.

Bovendien: password reset is OWASP's bekendste schiet-je-in-de-voet feature. Veelvoorkomende fouten:
1. **Voorspelbare tokens** (timestamp + email → kraakbaar)
2. **Geen token-expiry** of expiry te lang
3. **Account-enumeration** via foutmeldingen ("die email bestaat niet" vs "we hebben een mail gestuurd")
4. **Tokens niet eenmalig** — geldig na gebruik
5. **Geen rate-limiting** → bot kan 10.000 emails versturen via jouw flow naar willekeurige adressen
6. **Reset-link werkt over HTTP** → man-in-the-middle pakt token uit netwerk
7. **Old sessions blijven geldig** na password change → een aanvaller die al ingelogd is, blijft binnen
8. **Geen logging** → je weet niet wanneer iemands account succesvol/mislukt is reset

Dit plan dekt al deze gevallen af, en doet dat door **maximaal te leunen op wat Supabase Auth al biedt** in plaats van zelf crypto te schrijven. Eigen crypto = bug.

---

## Het goede nieuws: Supabase doet 80% al

Jouw stack gebruikt Supabase Auth als provider. Supabase heeft password reset volledig ingebouwd:

- **Token generatie** — secure random, server-side, niet voorspelbaar
- **Token storage** — in Supabase's auth schema, niet jouw zorg
- **Token expiry** — default 1 uur, configureerbaar
- **One-time-use** — Supabase invalideert token na succesvol gebruik
- **Email versturen** — Supabase heeft eigen SMTP of laat je je eigen SMTP koppelen (Postmark, Resend, SendGrid)
- **Audit log** — `auth.audit_log_entries` table in Supabase logt elke reset-poging

Wat jij moet bouwen: **de 2 frontend pagina's + 2 backend endpoints + de email template + de juiste configuratie**.

---

## Architectuur in 1 plaatje

```
┌─────────────────┐
│ User klikt      │
│ "Wachtwoord     │
│  vergeten"      │   1. POST /api/auth/forgot-password
│ in login modal  │──────────────────────────────┐
└─────────────────┘                              │
                                                 ▼
                                       ┌──────────────────┐
                                       │ Flask app.py     │
                                       │ - rate-limit     │
                                       │ - email-validate │
                                       │ - call Supabase  │
                                       └──────────────────┘
                                                 │
                                                 ▼
                                       ┌──────────────────┐
                                       │ Supabase Auth    │
                                       │ - genereert token│
                                       │ - stuurt email   │
                                       │   met reset-link │
                                       │   ?token=…       │
                                       └──────────────────┘
                                                 │
                                                 ▼
                                       ┌──────────────────┐
                                       │ User opent email │
                                       │ klikt link →     │
                                       │ /reset-password  │
                                       │ ?token=abc123    │
                                       └──────────────────┘
                                                 │
                                                 ▼
                                       ┌──────────────────┐
                                       │ Reset-pagina     │
                                       │ vraagt nieuw     │
                                       │ wachtwoord 2×    │
                                       └──────────────────┘
                                                 │
                                                 ▼ 2. POST /api/auth/reset-password
                                       ┌──────────────────┐
                                       │ Flask app.py     │
                                       │ - rate-limit     │
                                       │ - password-rules │
                                       │ - call Supabase  │
                                       └──────────────────┘
                                                 │
                                                 ▼
                                       ┌──────────────────┐
                                       │ Supabase Auth    │
                                       │ - verifieert tok │
                                       │ - hasht pw       │
                                       │ - update user    │
                                       │ - invalidate sess│
                                       └──────────────────┘
                                                 │
                                                 ▼
                                       Auto-login + redirect
                                       naar dashboard
```

---

## Fase 1 — Supabase configuratie (~30 min, 0 code)

Voordat we code schrijven, eerst Supabase juist instellen:

### 1.1 — Reset token TTL
Dashboard → **Authentication → Email Templates → Reset Password**
- Standaard staat de link op 1 uur — dat is goed (industrie-standaard)
- **Niet langer maken.** 24 uur is een security-anti-pattern voor reset flows

### 1.2 — Custom email template
Vervang Supabase's default templates door eigen Nederlandse versies in Clipdrop-stijl. Voorbeeld:

```html
<h2>Wachtwoord resetten — Clipdrop</h2>
<p>Hi {{ .Email }},</p>
<p>Je vroeg een nieuw wachtwoord aan voor je Clipdrop account.</p>
<p>Klik op deze knop om een nieuw wachtwoord te kiezen:</p>
<a href="{{ .ConfirmationURL }}"
   style="background:#e8b766;color:#1a1208;padding:12px 24px;
          border-radius:8px;text-decoration:none;font-weight:600">
  Nieuw wachtwoord kiezen
</a>
<p>De link is 1 uur geldig en kan maar 1× gebruikt worden.</p>
<p>Niet zelf aangevraagd? Negeer deze mail — er gebeurt niets met je account.</p>
<hr>
<small>Clipdrop · djclips.nl · Niet reageren op deze mail.</small>
```

### 1.3 — Redirect URL configureren
Dashboard → **Authentication → URL Configuration**
- **Site URL:** `https://djclips.nl` (productie)
- **Redirect URLs (allowlist):**
  - `https://djclips.nl/reset-password`
  - `http://127.0.0.1:5555/reset-password` (lokaal voor de desktop app)

**KRITIEK:** Zonder allowlist kan iemand een phishing-URL als reset-redirect injecteren. Supabase whitelist alleen exact deze URLs.

### 1.4 — Custom SMTP (later, na launch)
Standaard verstuurt Supabase via hun eigen mailserver met afzender `noreply@mail.app.supabase.io`. Dat lijkt onbetrouwbaar voor eindgebruikers (spam-flag).

Aanbeveling vóór beta-launch: koppel **Postmark** (transactional-email specialist, ~$15/mo voor 10k mails) of **Resend** (modern, $20/mo). Beide hebben gratis tiers voor de eerste maand. Daarmee komt de mail van `noreply@djclips.nl` af.

Dashboard → **Project Settings → Auth → SMTP Settings**

---

## Fase 2 — Backend endpoints (~1.5u code)

Twee nieuwe endpoints in `app.py`, beide aan `auth.py` koppelen.

### 2.1 — `POST /api/auth/forgot-password`

**Input:** `{ "email": "user@example.com" }`

**Logic (in auth.py → nieuwe `forgot_password(email)`):**
```python
def forgot_password(email):
    """Trigger Supabase to email a reset-link.

    SECURITY: We MUST return the same response whether the email exists
    or not, otherwise we leak which emails are registered (account
    enumeration vulnerability).
    """
    if supabase_client is None:
        return {'ok': True}  # don't leak config errors either

    # Basic email-format validation; reject obvious garbage.
    if not _is_valid_email(email):
        return {'ok': True}  # silent reject — looks identical to success

    try:
        supabase_client.auth.reset_password_email(
            email,
            options={
                'redirect_to': _reset_redirect_url(),
            }
        )
    except Exception as e:
        log.warning(f'reset_password_email failed for {email}: {e}')
        # Still return ok — never expose whether the call worked

    return {'ok': True}
```

**Endpoint (`app.py`):**
```python
@app.route('/api/auth/forgot-password', methods=['POST'])
@limiter.limit("3 per hour", key_func=_rate_limit_key)  # per-IP cap
@limiter.limit("5 per hour", key_func=lambda: f"email:{request.json.get('email','')}")
def api_forgot_password():
    """Always returns {ok: True} regardless of whether email exists."""
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    auth.forgot_password(email)
    return jsonify({'ok': True}), 200
```

**Belangrijk over de twee rate-limits samen:**
- **Per-IP: 3 per uur** stopt botnet die 1000 emails probeert vanaf één IP
- **Per-email: 5 per uur** stopt aanvaller die jouw inbox dichtgooit (5× reset-mail in 1 uur is meer dan genoeg legitiem)
- Beide tegelijk = je bent gedekt tegen IP-rotation én tegen targeted harassment

### 2.2 — `POST /api/auth/reset-password`

**Input:** `{ "access_token": "...", "refresh_token": "...", "new_password": "..." }`

De `access_token` komt uit het hash-fragment in de reset-URL (zie 3.2 hieronder).

**Logic (in auth.py → nieuwe `reset_password(access_token, refresh_token, new_password)`):**
```python
def reset_password(access_token, refresh_token, new_password):
    """Apply new password after user clicked reset-link.

    Supabase's flow: the link sets a temporary session in the browser via
    URL fragments. The frontend extracts access_token + refresh_token,
    sends them here, and we use them to authenticate the password update.
    """
    if supabase_client is None:
        return {'ok': False, 'error': 'Auth niet beschikbaar'}

    if not _is_strong_password(new_password):
        return {'ok': False, 'error': 'Wachtwoord voldoet niet aan eisen'}

    try:
        # Establish session from the recovery tokens
        sess = supabase_client.auth.set_session(access_token, refresh_token)
        if not sess or not sess.user:
            return {'ok': False, 'error': 'Reset-link ongeldig of verlopen'}

        # Now update the password while authenticated as that user
        result = supabase_client.auth.update_user({'password': new_password})
        if not result or not result.user:
            return {'ok': False, 'error': 'Update mislukt'}

        # KRITIEK: invalideer alle andere sessions zodat als iemand het
        # account al gehijackt had, die er nu uit ligt.
        try:
            supabase_admin.auth.admin.sign_out(sess.user.id, scope='others')
        except Exception as e:
            log.warning(f'sign_out other sessions failed: {e}')

        # Return new session so user is auto-logged-in
        return {
            'ok': True,
            'access_token':  result.session.access_token if result.session else None,
            'refresh_token': result.session.refresh_token if result.session else None,
            'user_id':       result.user.id,
            'email':         result.user.email,
        }
    except Exception as e:
        log.warning(f'reset_password failed: {e}')
        return {'ok': False, 'error': 'Reset mislukt'}
```

**Endpoint (`app.py`):**
```python
@app.route('/api/auth/reset-password', methods=['POST'])
@limiter.limit("5 per 10 minutes", key_func=_rate_limit_key)
def api_reset_password():
    data = request.get_json(silent=True) or {}
    res = auth.reset_password(
        data.get('access_token'),
        data.get('refresh_token'),
        data.get('new_password'),
    )
    return jsonify(res), (200 if res.get('ok') else 400)
```

### 2.3 — Helper functions in auth.py

```python
import re

_EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')

def _is_valid_email(email):
    return bool(email) and len(email) <= 254 and bool(_EMAIL_RE.match(email))

def _is_strong_password(pw):
    """Minimum: 8 chars, niet alleen letters, niet 'password' en kornuiten."""
    if not pw or len(pw) < 8 or len(pw) > 128:
        return False
    if pw.lower() in _COMMON_PASSWORDS:
        return False
    # Vereis tenminste 1 letter EN (1 cijfer OF 1 symbool)
    has_letter = any(c.isalpha() for c in pw)
    has_digit_or_sym = any(not c.isalpha() for c in pw)
    return has_letter and has_digit_or_sym

_COMMON_PASSWORDS = {
    'password', 'password1', '12345678', 'qwerty123', 'letmein1',
    'welcome1', 'admin123', 'clipdrop1', 'djclips01',
    # voeg toe na launch op basis van logs van geblokkeerde pogingen
}

def _reset_redirect_url():
    """Where Supabase redirects after user clicks the reset-link in email."""
    # Default: productie domain. Lokaal kan via env override.
    return os.getenv('RESET_REDIRECT_URL', 'https://djclips.nl/reset-password')
```

---

## Fase 3 — Frontend (~2u code)

Drie UI-componenten nodig:

### 3.1 — "Wachtwoord vergeten?" link in login-modal

In `static/index.html`, in de login form, een onopvallende link:

```html
<a href="#" class="ed-forgot-link" onclick="openForgotPasswordModal(event)">
  Wachtwoord vergeten?
</a>
```

### 3.2 — Forgot-password modal (in dezelfde index.html)

```html
<div class="modal" id="forgot-password-modal" hidden>
  <div class="modal-content">
    <h2>Wachtwoord resetten</h2>
    <p>Vul je email in. Als er een account bestaat met dat adres,
       sturen we je een link om een nieuw wachtwoord te kiezen.</p>
    <input type="email" id="forgot-email" placeholder="jouw@email.nl">
    <button onclick="submitForgotPassword()">Stuur reset-link</button>
    <div id="forgot-result" hidden>
      <strong>Check je inbox.</strong>
      Klik op de link in de email om een nieuw wachtwoord te kiezen.
      De link is 1 uur geldig.
    </div>
  </div>
</div>
```

JS:
```js
async function submitForgotPassword() {
  const email = document.getElementById('forgot-email').value.trim();
  if (!email) return;
  // ALWAYS show same message — never reveal whether email exists
  await fetch('/api/auth/forgot-password', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ email }),
  });
  document.getElementById('forgot-result').hidden = false;
}
```

### 3.3 — Reset-password pagina

**Optie A — Aparte HTML-pagina** `static/reset-password.html` (Recommended)

Voordeel: schoon gescheiden van de hoofdapp, geen interferentie met routing. Supabase plaatst de tokens in de URL-hash (`#access_token=xxx&refresh_token=yyy&type=recovery`) bij redirect na klik.

```html
<!DOCTYPE html>
<html lang="nl">
<head>
  <meta charset="utf-8">
  <title>Wachtwoord resetten — Clipdrop</title>
  <link rel="stylesheet" href="/static/style.css">
</head>
<body class="auth-page">
  <main>
    <h1>Kies een nieuw wachtwoord</h1>
    <form id="reset-form">
      <input type="password" id="new-pw" placeholder="Nieuw wachtwoord (min 8 tekens)"
             autocomplete="new-password" required minlength="8">
      <input type="password" id="confirm-pw" placeholder="Herhaal wachtwoord"
             autocomplete="new-password" required minlength="8">
      <button type="submit">Opslaan</button>
      <p id="reset-error" hidden></p>
    </form>
  </main>
  <script>
    // Extract tokens from URL fragment (Supabase places them after #)
    function parseHash() {
      const h = window.location.hash.slice(1);
      const params = new URLSearchParams(h);
      return {
        access_token:  params.get('access_token'),
        refresh_token: params.get('refresh_token'),
        type:          params.get('type'),
      };
    }

    const tokens = parseHash();
    if (tokens.type !== 'recovery' || !tokens.access_token) {
      document.body.innerHTML = '<main><h1>Link ongeldig of verlopen</h1>' +
        '<p>Vraag een nieuwe reset-link aan op de inlogpagina.</p></main>';
    }

    document.getElementById('reset-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const pw   = document.getElementById('new-pw').value;
      const conf = document.getElementById('confirm-pw').value;
      const err  = document.getElementById('reset-error');
      err.hidden = true;

      if (pw !== conf) {
        err.textContent = 'Wachtwoorden komen niet overeen';
        err.hidden = false;
        return;
      }
      if (pw.length < 8) {
        err.textContent = 'Minimaal 8 tekens';
        err.hidden = false;
        return;
      }

      const res = await fetch('/api/auth/reset-password', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          access_token:  tokens.access_token,
          refresh_token: tokens.refresh_token,
          new_password:  pw,
        }),
      });
      const body = await res.json();
      if (body.ok) {
        // Opslaan in localStorage zodat hoofdapp ingelogd is na redirect
        localStorage.setItem('cl_access',  body.access_token);
        localStorage.setItem('cl_refresh', body.refresh_token);
        window.location.href = '/';  // back to app, now logged in
      } else {
        err.textContent = body.error || 'Reset mislukt';
        err.hidden = false;
        // KRITIEK: wis URL-hash zodat tokens niet in browser-history blijven
        history.replaceState(null, '', window.location.pathname);
      }
    });

    // Wis hash zodra de pagina geladen is, zodat tokens niet in
    // browser-history/screenshot zichtbaar blijven.
    setTimeout(() => {
      history.replaceState(null, '', window.location.pathname);
    }, 100);
  </script>
</body>
</html>
```

Flask serveert dat automatisch via `static_url_path` — geen route nodig, alleen het bestand op disk zetten.

**Optie B — Sectie in de hoofd-index.html** met `?reset` URL-parameter
Minder schoon, meer kans op routing-bugs. Niet doen tenzij hoofdapp echt single-page moet zijn.

### 3.4 — Hash-clear meteen na laden

Zoals in 3.3 staat: **wis de hash binnen 100ms na page-load**. Anders blijven `access_token` en `refresh_token` zichtbaar in:
- Browser-history
- Tab-titel-tooltip
- Per ongeluk gedeelde screenshots
- Plugins die URLs loggen

`history.replaceState(null, '', window.location.pathname)` is de juiste call.

---

## Fase 4 — Security checklist (verifieer vóór live-zetten)

Loop dit lijstje af na implementatie. Elke regel is een poging tot misbruik die we moeten weerstaan:

| # | Test | Verwacht |
|---|---|---|
| 1 | POST `/api/auth/forgot-password` met onbestaande email | `{ok: true}` (dezelfde response als met bestaande email) |
| 2 | POST `/api/auth/forgot-password` 4× snel achter elkaar met geldige email | 4e call krijgt `429 Too Many Requests` |
| 3 | POST `/api/auth/forgot-password` met `email: ""` | `{ok: true}` (geen 500-error die enumeration mogelijk maakt) |
| 4 | POST `/api/auth/forgot-password` met `email: "<script>alert(1)</script>"` | `{ok: true}` (validation rejet, geen XSS in email) |
| 5 | Klik reset-link 2× in dezelfde mail | 2e klik: "Link ongeldig of verlopen" (Supabase invalidate) |
| 6 | Wacht 90 min na ontvangst, klik dan reset-link | "Link ongeldig of verlopen" (expiry werkt) |
| 7 | Reset-link openen via HTTP ipv HTTPS | Redirect naar HTTPS (vercel.json header `Strict-Transport-Security`) |
| 8 | Reset-pagina opent zonder hash-tokens | Toon "Link ongeldig" — geen reset-form |
| 9 | URL-hash na page-load checken | Hash is leeg binnen 100ms |
| 10 | Reset met `new_password: "abc"` | `{ok: false}` — minlength 8 |
| 11 | Reset met `new_password: "password"` | `{ok: false}` — common-password blacklist |
| 12 | Reset met `new_password: "12345678"` | `{ok: false}` — alleen cijfers, geen letters |
| 13 | Login in tab A, vraag reset in tab B, reset via mail | Tab A's sessie blijft werken (Supabase invalidate alleen `scope='others'` — eigen sessie blijft) |
| 14 | Login op laptop, login op telefoon, reset via mail op telefoon | Laptop wordt automatisch uitgelogd bij volgende API-call (sign_out others) |
| 15 | Reset-mail komt binnen | Van `noreply@djclips.nl` (post-SMTP-config), niet `noreply@mail.app.supabase.io` |
| 16 | Bekijk Supabase auth.audit_log_entries na reset | Logt `password_recovery_requested` + `password_updated` events met IP |

---

## Fase 5 — Edge cases en niet-vergeten dingen

### 5.1 — Email confirmation users
Als `email_confirmed_at IS NULL` (gebruiker heeft signup-mail nooit bevestigd), wat doet Supabase dan met de reset-link? **Standaardgedrag:** verstuurt nog steeds. Sommige flows willen dat dat wordt geblokkeerd. Beslis: voor jouw beta is "altijd toestaan" prima.

### 5.2 — Account verwijderd
Wat als gebruiker reset-link opent maar zijn account is intussen door jou verwijderd? Supabase returnt error, jouw frontend toont "Link ongeldig" — correct gedrag.

### 5.3 — Reset-vraag terwijl gebruiker al ingelogd is
Edge case: iemand zit ingelogd in tab A en klikt "Wachtwoord vergeten" in tab B (bv. nieuwsgierig). Niet blokkeren, niet automatisch uitloggen — gewoon de flow laten lopen. Na succes wordt sessie A overschreven door 5.4.

### 5.4 — Old sessions invalidate
Standaard logt Supabase **alle sessies behalve de huidige** uit na password change. Dit is in `reset_password()` boven al gedekt met `scope='others'`. Verifieer in productie of dit ook echt zo werkt — Supabase wijzigt API's vaker dan ik zou willen.

### 5.5 — Bundled desktop-app
De `.dmg` versie van Clip Live draait op `http://127.0.0.1:5555`. Reset-mail moet daar óók naartoe kunnen linken voor lokale ontwikkeling/testing. Twee opties:

**A.** Twee verschillende reset-URLs in Supabase allowlist (`https://djclips.nl/reset-password` + `http://127.0.0.1:5555/reset-password`)

**B.** Reset-link wijst altijd naar `https://djclips.nl/reset-password`, en die pagina detecteert of de gebruiker eigenlijk de desktop-app gebruikt en redirect dan naar `http://127.0.0.1:5555/reset-password#...`. Lastiger.

**Aanbeveling:** A. Eenvoudig en explicieter.

### 5.6 — Audit & alerting
Op den duur (niet voor v1) wil je in Supabase logs zoeken naar abnormale patronen:
- 100+ `password_recovery_requested` events van 1 IP → automatisch blokkeren (al gedekt door rate-limit)
- 10+ reset-requests voor 1 email in 24u → flag account, mogelijk doelwit
- Reset gevolgd door login uit ander land binnen 5 min → security-mail naar gebruiker ("we zagen een ongebruikelijke login")

Dit gaat naar v2.

---

## Effort & beslispunten

| Fase | Wat | Effort |
|---|---|---|
| 1 | Supabase configuratie (email template, redirect-URLs) | 0.5 u |
| 2 | Backend: 2 endpoints + helpers in auth.py | 1.5 u |
| 3 | Frontend: forgot-modal + reset-pagina | 2.0 u |
| 4 | Security checklist doorlopen + fixes | 1.0 u |
| 5 | SMTP koppelen (Postmark/Resend) | 0.5 u (na launch optioneel uit te stellen) |
| | **Totaal** | **~5.5 u** |

### Beslispunten voor Sjuul

**P1.** SMTP-provider keuze:
- **Postmark** — premium, beste deliverability, $15/mo
- **Resend** — modern, developer-friendly, $20/mo na free tier
- **Supabase default eerst** — gratis, accept dat sommige mails in spam komen tot we upgraden

**P2.** Reset-token TTL: blijven op 1 uur (Supabase default) of korter (30 min, strenger)?

**P3.** Password rules (zie `_is_strong_password()`):
- Mijn voorstel: 8+ chars, niet uit common-list, minstens 1 letter + 1 cijfer-of-symbool
- Stricter mogelijk: 12+ chars, hoofdletter, cijfer, symbool — gebruikers haten dit, zegt onderzoek
- Wat is jouw voorkeur?

**P4.** Bouwen vóór of na launch?
- **Vóór launch (aanbevolen):** beta-users hebben de feature direct nodig, je hebt geen handmatige reset-acties
- **Na launch:** workaround = jij reset handmatig via Supabase dashboard. Werkt voor 1-5 testers maar schaalt niet

---

## Volgorde van bouwen

Als we dit gaan implementeren — niet nu, maar in een dedicated sessie — dan deze volgorde aanhouden:

1. Supabase config (Fase 1) — 30 min, niets te breken
2. Backend endpoints (Fase 2) — eerst lokaal testen met curl, niet via UI
3. Curl-test:
   ```
   curl -X POST http://127.0.0.1:5555/api/auth/forgot-password \
        -H 'Content-Type: application/json' \
        -d '{"email":"test@example.com"}'
   ```
   Moet `{"ok":true}` returnen of email nu wel/niet bestaat.
4. Mail-flow testen: registreer testaccount → forgot → kijk in inbox → klik link → check redirect
5. Frontend bouwen (Fase 3) zodra backend bewezen werkt
6. Security checklist (Fase 4) doorlopen
7. Pas dán naar productie (na DNS-koppeling van djclips.nl in Cloudflare)

---

## Niet vergeten na launch

- Monitor Supabase auth.audit_log_entries de eerste week — kijk of er rare patronen zijn
- Voeg gemelde common-passwords toe aan `_COMMON_PASSWORDS` set op basis van logs
- Overweeg passkeys (WebAuthn) als v2 — schakel het wachtwoord helemaal uit, gebruiker logt in met TouchID/FaceID. Supabase ondersteunt dit sinds 2024
