# Plan 2026-05-28: OAuth login (Google + Apple + Spotify)

> Doel: gebruikers laten inloggen/registreren via Google primair (met Apple en Spotify als secundaire opties), naast de bestaande Supabase email/wachtwoord-flow.

## SAMENVATTING

| Beslissing | Keuze |
|---|---|
| Primaire CTA login + signup | Continue with Google (groot, bovenaan) |
| Secundair | Continue with Apple, Continue with Spotify, dan divider, dan email/password |
| Email-collision strategy | Supabase default: separate accounts. Nette UX-melding bij conflict |
| Tijdlijn | Productie, na omnidj.com live |
| Spotify-data harvest | Profile + top artists + top tracks + product (free/premium). Opslaan in Supabase. GDPR-vermelding in privacy-policy |
| Apple Sign In | Ja, naast Google (vereist Apple Developer Account €99/jaar) |

---

## ARCHITECTUUR

Supabase Auth ondersteunt OAuth providers out-of-the-box via de "Providers" tab in dashboard. Geen extra backend-code nodig voor de token-exchange — Supabase handelt PKCE-flow + token-refresh af. Wel custom werk:

1. Provider-config in Supabase dashboard (Google, Apple, Spotify aanzetten + client-IDs invullen)
2. Frontend "Continue with X" buttons op login + signup
3. Callback handler in onze app (`/auth/callback`) die de Supabase-session sluit en doorroutet
4. Voor Spotify: na succesvol login eenmalig profile + tops fetchen + opslaan in Supabase `user_extended_profile` tabel
5. Voor Apple: 2FA + private-relay-email handling

---

## FASE 1: Google OAuth (4-6u dev + 1-2u config)

### 1.1 Supabase dashboard (15 min — Sjuul)

1. Ga naar [Google Cloud Console](https://console.cloud.google.com) → nieuw project of bestaand "Omni DJ"
2. APIs & Services → OAuth consent screen → External, fill in:
   - App name: Omni DJ
   - User support email: omnidj@monohq-labs.com
   - Authorized domains: `omnidj.com`, `supabase.co`
   - Developer contact: omnidj@monohq-labs.com
3. Credentials → Create credentials → OAuth client ID:
   - Application type: Web application
   - Name: Omni DJ Web
   - Authorized JavaScript origins: `https://omnidj.com`, `https://www.omnidj.com`, `http://127.0.0.1:5555` (dev)
   - Authorized redirect URIs: `https://<your-supabase-project>.supabase.co/auth/v1/callback`
4. Save client ID + client secret.
5. In Supabase dashboard: Authentication → Providers → Google → Enable, paste client ID + secret. Save.

### 1.2 Frontend: signin button + handler (3-4u dev)

**A. Login-overlay redesign (auth-overlay):**

Bovenaan, na "Omni DJ" wordmark:

```html
<button class="auth-oauth-btn auth-oauth-google" data-provider="google">
  <svg class="oauth-icon" viewBox="0 0 24 24">...Google G logo...</svg>
  <span>Continue with Google</span>
</button>
<button class="auth-oauth-btn auth-oauth-apple" data-provider="apple">
  <svg>...Apple logo...</svg>
  <span>Continue with Apple</span>
</button>
<button class="auth-oauth-btn auth-oauth-spotify" data-provider="spotify">
  <svg>...Spotify logo...</svg>
  <span>Continue with Spotify</span>
</button>
<div class="auth-divider"><span>or use email</span></div>
<!-- bestaande Log in / Sign up tab + form blijft hieronder -->
```

**B. JS handler:**

```javascript
document.querySelectorAll('.auth-oauth-btn').forEach(function(btn){
  btn.addEventListener('click', async function(){
    var provider = btn.dataset.provider;
    // Call our backend, which delegates to Supabase Auth
    try {
      const r = await fetch('/api/auth/oauth-start', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({provider: provider, redirect_to: window.location.origin + '/auth/callback'})
      });
      const data = await r.json();
      if (data.url) window.location.href = data.url;
      else throw new Error(data.error || 'OAuth start failed');
    } catch(e){
      showAuthError('Could not start ' + provider + ' login: ' + e.message);
    }
  });
});
```

**C. Backend endpoint (`app.py`):**

```python
@app.route('/api/auth/oauth-start', methods=['POST'])
@limiter.limit("30 per hour", key_func=_rate_limit_key)
def api_auth_oauth_start():
    data = request.get_json(silent=True) or {}
    provider = data.get('provider')
    redirect_to = data.get('redirect_to')
    if provider not in ('google', 'apple', 'spotify'):
        return jsonify({'ok': False, 'error': 'Unsupported provider'}), 400
    if not redirect_to or not redirect_to.startswith(('http://127.0.0.1:', 'https://omnidj.com', 'https://www.omnidj.com')):
        return jsonify({'ok': False, 'error': 'Invalid redirect URL'}), 400
    # Generate Supabase OAuth URL
    sb_url = f"{SUPABASE_URL}/auth/v1/authorize?provider={provider}&redirect_to={urllib.parse.quote(redirect_to)}"
    return jsonify({'ok': True, 'url': sb_url})
```

**D. Callback handler:**

Nieuwe route `/auth/callback`:

```python
@app.route('/auth/callback')
def auth_callback():
    # Supabase returns access_token + refresh_token in URL fragment (#access_token=...)
    # We serve a minimal HTML page that grabs them via JS and POSTs to /api/auth/exchange
    return send_from_directory('static', 'auth-callback.html')
```

`auth-callback.html`:

```html
<!DOCTYPE html>
<html><head><title>Logging in…</title></head><body>
<p>Logging you in…</p>
<script>
(async function(){
  // Parse URL hash for access_token + refresh_token (Supabase implicit flow)
  var hash = window.location.hash.substring(1);
  var params = new URLSearchParams(hash);
  var access_token = params.get('access_token');
  var refresh_token = params.get('refresh_token');
  if (!access_token) {
    document.body.innerHTML = '<p>Login failed: no token returned.</p>';
    return;
  }
  // Persist to our localStorage key so the main app's existing session-loader picks it up
  var session = {
    access_token: access_token,
    refresh_token: refresh_token,
    expires_at: parseInt(params.get('expires_at') || '0', 10),
    token_type: params.get('token_type') || 'bearer'
  };
  localStorage.setItem('omniDj.session', JSON.stringify(session));
  // For Spotify: fetch profile + tops once (see Fase 3)
  // Then redirect to home
  window.location.href = '/';
})();
</script>
</body></html>
```

### 1.3 Email-collision handling (1u)

Supabase's default: zelfde email maar verschillend provider = nieuwe user. Geen technische conflict, wel UX-conflict.

**Detectie**: na callback, fetch /api/auth/me. Als er een user wordt teruggegeven (succes), check `user_metadata.providers` of `app_metadata.providers`. Als de user nu Google heeft, maar bij signup destijds via email had ingelogd, was 't een nieuwe user.

**UX**:
- Bij de eerste Google-login: redirect naar onboarding-wizard (zoals nu sectie 1-4)
- Bij detectie van conflict: toon banner "We zien dat je eerder met email/wachtwoord hebt ingelogd op deze email. Wil je accounts samenvoegen?" → link naar account-settings (later: account-merge button als feature)

Voor v1 accepteren we de separate accounts. Account-merge is een aparte mini-feature voor sessie 60+.

---

## FASE 2: Apple Sign In (3-4u dev + Apple Developer setup)

### 2.1 Apple Developer Account (Sjuul, eenmalig €99/jaar)

1. [developer.apple.com](https://developer.apple.com) → enroll
2. Certificates, Identifiers & Profiles → Identifiers → nieuw App ID:
   - Name: Omni DJ
   - Bundle ID: `com.monolabs.omnidj` (toekomstige bundle)
3. Services ID nieuw:
   - Identifier: `com.monolabs.omnidj.web`
   - Sign In with Apple → enable
   - Configure: Primary App ID = je net gemaakte App ID, return URLs = `https://<supabase-project>.supabase.co/auth/v1/callback`
4. Keys → nieuw Key voor Sign In with Apple. Download de .p8 file (krijg je 1× te zien).
5. Supabase dashboard → Auth → Providers → Apple → Enable, paste Service ID + Team ID + Key ID + Private Key (.p8 content).

### 2.2 Apple-specific gotcha's

- **Private-relay email**: Apple kan een random `xxx@privaterelay.appleid.com` adres teruggeven als gebruiker zijn echte email verbergt. Voor onze app betekent dat: email-veld bestaat, maar werkt alleen via Apple's forwarding. Geen issue voor login, wel iets om in UX te noemen ("Je email wordt door Apple verborgen — alle communicatie loopt via Apple Relay").
- **2FA inherently**: Apple Sign In heeft altijd Apple's 2FA achter zich. Geen extra setup nodig.

### 2.3 Frontend

Dezelfde `.auth-oauth-btn` structuur. Apple's HIG vereist een specifiek logo + styling — gebruik [Apple's branding guidelines](https://developer.apple.com/design/human-interface-guidelines/sign-in-with-apple).

---

## FASE 3: Spotify OAuth + data-harvest (5-7u dev)

### 3.1 Spotify Developer App (15 min — Sjuul)

1. [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard) → Create app
2. Name: Omni DJ
3. Redirect URIs: `https://<supabase-project>.supabase.co/auth/v1/callback`
4. APIs used: Web API
5. Save Client ID + Client Secret
6. In Supabase: Auth → Providers → custom OAuth provider toevoegen voor Spotify (Supabase heeft Spotify NIET als built-in provider, dus we gebruiken "Custom OAuth Provider"):
   - Provider name: spotify
   - Authorization URL: `https://accounts.spotify.com/authorize`
   - Token URL: `https://accounts.spotify.com/api/token`
   - User info URL: `https://api.spotify.com/v1/me`
   - Scopes: `user-read-private user-read-email user-top-read user-read-recently-played`

### 3.2 Data-harvest na Spotify login

In `auth-callback.html` (na token-persist):

```javascript
// Spotify-specifiek: fetch profile + tops, save to backend
if (params.get('provider') === 'spotify') {
  var spotifyToken = params.get('provider_token'); // Supabase passt 'm door
  if (spotifyToken) {
    await fetch('/api/auth/spotify-enrich', {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer ' + access_token,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({spotify_token: spotifyToken})
    });
  }
}
```

Backend endpoint:

```python
@app.route('/api/auth/spotify-enrich', methods=['POST'])
@limiter.limit("5 per hour", key_func=_rate_limit_key)
def api_auth_spotify_enrich():
    user_info, err = _require_authed_user()
    if err: return err
    data = request.get_json(silent=True) or {}
    spotify_token = data.get('spotify_token')
    if not spotify_token: return jsonify({'ok': False, 'error': 'No Spotify token'}), 400

    # Fetch from Spotify Web API
    headers = {'Authorization': f'Bearer {spotify_token}'}
    profile = requests.get('https://api.spotify.com/v1/me', headers=headers, timeout=10).json()
    top_artists = requests.get('https://api.spotify.com/v1/me/top/artists?limit=20&time_range=medium_term', headers=headers, timeout=10).json()
    top_tracks = requests.get('https://api.spotify.com/v1/me/top/tracks?limit=20&time_range=medium_term', headers=headers, timeout=10).json()
    recent = requests.get('https://api.spotify.com/v1/me/player/recently-played?limit=20', headers=headers, timeout=10).json()

    # Persist to Supabase via service-role
    payload = {
        'user_id': user_info['user_id'],
        'spotify_id': profile.get('id'),
        'display_name': profile.get('display_name'),
        'product': profile.get('product'),  # free / premium
        'country': profile.get('country'),
        'followers': profile.get('followers', {}).get('total'),
        'top_artists_json': top_artists.get('items', []),
        'top_tracks_json': top_tracks.get('items', []),
        'recent_played_json': recent.get('items', []),
        'enriched_at': datetime.utcnow().isoformat()
    }
    # ... insert/update into spotify_user_data table
    return jsonify({'ok': True})
```

### 3.3 Supabase tabel `spotify_user_data`

Migration file `supabase/migrations/002_spotify_user_data.sql`:

```sql
CREATE TABLE IF NOT EXISTS spotify_user_data (
  user_id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  spotify_id text,
  display_name text,
  product text,
  country text,
  followers int,
  top_artists_json jsonb,
  top_tracks_json jsonb,
  recent_played_json jsonb,
  enriched_at timestamptz NOT NULL DEFAULT now(),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE spotify_user_data ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users read own spotify data"
  ON spotify_user_data FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "service role writes spotify data"
  ON spotify_user_data FOR ALL
  USING (auth.role() = 'service_role');
```

### 3.4 Wat je hiermee kunt zien als platform-owner

Backend admin-query:

```sql
-- Genre-distributie van je gebruikers
SELECT
  jsonb_array_elements(top_artists_json->'items')->>'genres' AS genres,
  count(*) AS n_users
FROM spotify_user_data
GROUP BY genres
ORDER BY n_users DESC;

-- Free vs Premium ratio
SELECT product, count(*) FROM spotify_user_data GROUP BY product;

-- Active DJ proxy: users with >10 unique artists in recent_played
SELECT user_id, jsonb_array_length(recent_played_json) AS recent_n
FROM spotify_user_data WHERE jsonb_array_length(recent_played_json) > 10
ORDER BY recent_n DESC LIMIT 20;
```

Dit is goudwaard voor:
- Onboarding-personalisatie (suggesteer brand-stack op basis van genre)
- Feature-prioritering (welke artiesten zien je users vooral?)
- Marketing (welke kanalen targetten obv country + product-type)

### 3.5 Privacy-policy update vereist

Je moet **vóór je dit live zet** in je privacy-policy melden:
- Welke Spotify-data je verzamelt (profile + tops + recent played)
- Waarvoor (product-verbetering, geen verkoop aan derden)
- Hoe gebruikers het kunnen verwijderen (delete-account in Settings)
- Bewaartermijn (suggest: refreshen elke 30 dagen, anders permanent gekoppeld zolang account bestaat)

Spotify Developer Terms of Service §IV.2 vereist expliciete consent voor het opslaan van user data buiten Spotify's eigen API-cache. Hou je daar aan, anders Spotify-app-disconnect-risico.

---

## VOLGORDE VAN UITVOERING

### Volgorde A — Veiligste (mijn aanbeveling)

1. **Sessie 60**: omnidj.com live + Stripe live mode (uit reeds bestaand plan)
2. **Sessie 61**: Fase 1 Google OAuth (4-6u). Test op productie-domain.
3. **Sessie 62**: Fase 2 Apple Sign In (3-4u). Apple Developer account aanvragen kan al eerder starten (1-7 dagen approval).
4. **Sessie 63**: Privacy-policy update + Fase 3 Spotify OAuth + data-harvest (5-7u).

### Volgorde B — Sneller maar 2× config-werk

1. **Nu**: Fase 1 Google OAuth dev-only (127.0.0.1:5555). Test functioneel.
2. **Sessie 60**: omnidj.com live → herconfigureer redirect-URIs in Google Cloud + Supabase.
3. **Sessie 61+**: Apple + Spotify.

### Geschatte total dev-tijd

| Fase | Dev | Externe setup (Sjuul) |
|---|---|---|
| Fase 1 Google | 4-6u | 30 min Google Cloud |
| Fase 2 Apple | 3-4u | €99 + 1-7d approval + 30 min |
| Fase 3 Spotify + harvest | 5-7u | 15 min Spotify dashboard + privacy-policy update |
| **Totaal** | **12-17u dev** | **~2u externe acties + €99** |

---

## OPEN BESLISSINGEN VOOR SJUUL

1. **Volgorde A of B?** (productie-first vs dev-first)
2. **Apple Developer Account aanvragen nu of later?** (lange lead-time, dus eerder = beter)
3. **Account-merge feature** (oude email+pwd + nieuwe Google met zelfde email): v1 = separate accounts, of meteen merge-button bouwen?
4. **Spotify data-bewaartermijn**: 30 dagen / 6 maanden / 1 jaar / permanent zolang user account heeft?
5. **Privacy-policy schrijven**: zelf doen, AI laten genereren, of jurist?

---

## RISICO'S + MITIGATIES

| Risico | Kans | Impact | Mitigatie |
|---|---|---|---|
| OAuth redirect-URL mismatch tussen dev en prod | Hoog | Loginflow breekt | Twee Google Cloud projects: "Omni DJ Dev" (127.0.0.1) + "Omni DJ Prod" (omnidj.com) |
| User-conflict bij email-collision | Middel | UX-verwarring | UX-banner met merge-suggestion + duidelijke "log in via email" fallback |
| Spotify rate-limit overshoot bij harvest | Laag | Trage onboarding | Cache 30 dagen, achteraf refreshen via cron |
| Apple private-relay email verloopt | Middel | User kan emails niet meer ontvangen | Detecteer privaterelay.appleid.com en toon banner "Verifieer je echte email voor critical notifications" |
| Spotify policy-takedown door geen privacy-policy | Hoog (bij launch) | Spotify-integratie offline | Privacy-policy LIVE voor productie-launch, niet "later" |

---

## INSCHATTING IMPACT OP HUIDIGE CODEBASE

Wijzigingen in `static/index.html`:
- Auth-overlay DOM: +3 oauth-buttons + divider + minor CSS
- Auth callback handler: nieuwe `auth-callback.html` (klein bestand)

Wijzigingen in `app.py`:
- `/api/auth/oauth-start` endpoint
- `/auth/callback` route (serveert HTML)
- `/api/auth/spotify-enrich` endpoint (Fase 3)
- Import: `urllib.parse`, `requests` (al present)

Wijzigingen in Supabase:
- `supabase/migrations/002_spotify_user_data.sql` (Fase 3)
- Dashboard config voor 3 providers (geen code)

Risico op breuk in bestaande flow: **laag**. We voegen alleen toe, raken email/wachtwoord-flow niet.
