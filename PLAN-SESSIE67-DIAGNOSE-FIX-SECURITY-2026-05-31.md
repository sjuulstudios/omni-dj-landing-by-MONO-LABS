# Plan: login-blocker fix + install-check + security-ronde

> Sessie 67 (2026-05-31). Onderzoek + plan. Nog NIETS gewijzigd.
> Alles hieronder is geverifieerd in code / live Supabase, niet vermoed.

---

## TL;DR (in 5 zinnen)

1. De "login/upload-blocker" is GEEN bug: het admin-account `business@sjuulstudios.com`
   heeft sinds 8 mei niet meer succesvol ingelogd, dus het wachtwoord klopt niet meer.
   Inloggen met het juiste wachtwoord (of een reset) lost het op.
2. De ffmpeg-fix (static binaries) is correct en compleet; alleen de drawtext-detectie
   in cutter.py heeft een kosmetische 1-regel-bug die captions stilletjes uitzet.
3. Voor de install heeft een beta-tester NIETS extra nodig: ffmpeg zit in de .app,
   geen Homebrew, geen losse downloads.
4. De security is voor een snel-gebouwde app verrassend net: geen secrets in git of in
   de bundle, RLS staat aan en is goed dichtgetimmerd, geen shell-injection, paden netjes
   gevalideerd.
5. Er zijn 4 kleine security-verbeteringen (geen van allen kritiek) plus 3 Supabase-warnings.

---

## DEEL 1 — De login/upload-blocker (de "fix" die je vroeg)

### Wat HANDOVER zei
"In de app gebeurt niks bij upload; STATE.session blijft leeg; `/api/upload-local` geeft 401;
directe login geeft 'Invalid login credentials'."

### Wat ik heb vastgesteld (live in de Supabase-database gekeken)
- Account `business@sjuulstudios.com` bestaat, e-mail bevestigd, **role=admin, plan=pro**.
  Maar `last_sign_in_at` staat nog op **8 mei** (de aanmaakdatum). Sinds 8 mei is er dus
  geen enkele geslaagde login meer op dit account. Elke poging sindsdien faalde =
  verkeerd wachtwoord.
- Tegelijk logde `business+dmgtest1@sjuulstudios.com` (plan=studio) **vandaag 19:07 wél
  succesvol in**. De backend, Supabase en de inlog-keten werken dus aantoonbaar.
- De frontend-code (`static/index.html` ~24842) is correct: bij `ok:true` slaat hij de
  tokens op; bij `ok:false` blijft `STATE.session` leeg en zie je precies het symptoom
  dat je beschreef.

### Conclusie
Geen code-bug. Het is een wachtwoord-/account-kwestie. STATE.session blijft leeg omdat de
login simpelweg faalt (fout wachtwoord), niet omdat de app stuk is.

### Fix (kies 1)
- **A. Juist wachtwoord (snelst).** Log in met `business@sjuulstudios.com` + het echte
  wachtwoord. Lukt dat → upload werkt meteen.
- **B. Wachtwoord resetten.** Weet je het niet meer: gebruik "Forgot password" in de app,
  of ik reset het admin-wachtwoord via de Supabase admin-API (jij geeft een nieuw wachtwoord,
  ik zet het). Dit raakt geen code.
- **C. Test met een werkend account.** `business+dmgtest1@sjuulstudios.com` werkt al; daarmee
  kun je de hele keten (login → upload → analyse) nu al testen los van het admin-account.

> Aanbeveling: eerst B of C om te bevestigen dat upload werkt, daarna admin-wachtwoord netjes
> zetten. Geen rebuild nodig voor deze stap.

---

## DEEL 2 — ffmpeg / install-dependencies (wat heeft een tester nodig?)

### ffmpeg-bundeling: correct en af
- `vendor/ffmpeg/ffmpeg` + `ffprobe` zijn **static arm64 builds** (Martin-Riedl). Geverifieerd:
  geen `/opt/homebrew`-paden in de binary, Mach-O arm64.
- `build_macos.sh` kopieert deze static binaries naar `Resources/bin/` en heeft een vangrail
  die de build laat falen als er tóch externe dylibs in zitten. Goed.
- `media_tools.py` resolvet ffmpeg/ffprobe naar het bundle-pad met PATH-fallback; `app.py` en
  `cutter.py` gebruiken dit overal consistent (geen kale `'ffmpeg'`-calls meer in de hot paths).

### Wat een beta-tester op een verse Mac nodig heeft: NIETS extra
- ffmpeg/ffprobe → in de .app.
- Python + alle libs (flask, librosa, supabase, stripe, …) → in de .app (PyInstaller).
- Supabase/Stripe publieke keys → hardcoded in `runtime_config.py` (alleen publieke waarden,
  geen secrets). Geen `.env` nodig naast de app.
- Geen Homebrew, geen losse ffmpeg-download, geen `pip install`.
- Mac vereiste: **Apple Silicon (arm64), macOS 11+**. (Intel-Macs werken NIET — de static
  ffmpeg en de build zijn arm64-only. Universal2 is een latere stap.)

### Eén bekende, kleine ffmpeg-bug (captions)
`cutter.py` `_ffmpeg_has_drawtext()` (~regel 253) controleert of het `drawtext`-filter bestaat
met een te strak patroon (`'T..  drawtext'`, dubbele spatie). De Martin-Riedl ffmpeg print de
regel net iets anders, waardoor de app denkt dat drawtext ontbreekt en **captions stilletjes
overslaat**. Het filter zit er wél in.
**Fix:** match verruimen naar een losse check op het woord `drawtext` in de filterlijst
(1 regel). Daarna captions bevestigen via een export-test.

### Optionele features die NIET in de bundle zitten (bewust)
- Auto-tracking (person detection): `opencv`, `ultralytics`, `pyobjc-Vision` zijn uitgesloten
  (scheelt ~2 GB). De app valt netjes terug met een install-hint i.p.v. te crashen. Prima voor
  beta; later eventueel een "Pro"-download met tracking.
- `torch`/`demucs` (AI source separation) en YouTube-upload idem uitgesloten.

---

## DEEL 3 — Security-ronde (vibecode-checklist + online research)

Ik heb de bekende valkuilen voor snel-gebouwde / AI-gebouwde apps afgelopen
(missing RLS, exposed service_role key, secrets in bundle, command injection, path traversal,
debug-mode, CORS). Bevindingen:

### ✅ Wat GOED zit (geen actie)
- **Geen secrets in git.** `.env` is gitignored en is nooit in de history gecommit
  (`git log --all` op `.env` is leeg). De enige "secret-achtige" match in tracked code is de
  secret-scanner in `build_macos.sh` zelf.
- **Geen secrets in de .app-bundle.** Geen `sk_test`-waarde, geen service_role-JWT, geen
  `whsec_` in `dist/`. Alleen publieke keys via `runtime_config.py`.
- **RLS staat AAN** op beide tabellen (`profiles`, `audit_logs`) en de policies zijn correct:
  - lezen/wijzigen alleen eigen rij (`auth.uid() = id`);
  - de UPDATE-policy **blokkeert** dat een user zijn eigen `plan`, `role`, `usage`,
    `quota_reset_date` of `stripe_*` aanpast. Dit is precies de valkuil die de meeste
    vibecode-apps wél hebben (self-upgrade naar admin/studio) — hier dichtgetimmerd.
- **Geen command-injection.** Nergens `shell=True` / `os.system`; alle ffmpeg-calls gaan via
  lijst-argumenten.
- **Geen path-traversal in file-serving.** Filenames worden `os.path.basename()`-gestript,
  bron-paden komen uit vertrouwde job-state, en elke serve-route heeft een `_require_job_access`
  auth-gate.
- **Export-map whitelist.** Export mag alleen binnen de home-map (realpath + symlink-check),
  dus geen schrijven naar `/etc`, `/System`, `/Library`.
- **Flask draait met `debug=False`** en bindt op **127.0.0.1** (loopback), niet 0.0.0.0.
- **Wachtwoordbeleid** (NIST-stijl: lengte + blacklist) en **rate-limiting** op auth-endpoints.

### ⚠️ Wat BETER kan (geen kritiek, prioriteit van hoog naar laag)

**S1. DNS-rebinding / CSRF op de lokale server (laag-midden risico).**
De app luistert op `127.0.0.1:5555` zonder Host-header-check of CSRF-token. Een kwaadaardige
website die je open hebt staan kan in theorie POST's naar `http://127.0.0.1:5555/api/...`
sturen (of via DNS-rebinding de loopback bereiken) en bv. een upload-job aanmaken of een
lokaal bestand laten registreren. Praktisch risico is beperkt (single-user desktop, auth-token
nodig voor de meeste acties), maar het is de enige echte "remote" vector.
**Fix-opties:** (a) Host-header valideren (alleen `127.0.0.1:5555`/`localhost:5555`
accepteren) als `@app.before_request`; (b) een `Origin`/`Sec-Fetch-Site`-check op state-changing
endpoints. ~20-30 regels, geen UI-impact.

**S2. `/api/upload-local` accepteert elk absoluut pad (laag risico, single-user).**
Een ingelogde gebruiker (of via S1 een kwaadaardige pagina mét token) kan elk absoluut pad
op de Mac registreren dat ffprobe als media accepteert. Op een single-user desktop is dat je
eigen bestand, dus laag. Maar gecombineerd met S1 wordt het relevanter.
**Fix:** zelfde home-whitelist als de export-map toepassen op de input-pad-check.

**S3. Supabase: 3 security-warnings van de linter (laag, snel op te lossen):**
- *Leaked Password Protection staat uit* → 1 klik aan in Supabase (Auth → Policies):
  checkt wachtwoorden tegen HaveIBeenPwned. Aanrader vóór publieke launch.
- *`handle_new_user()` en `rls_auto_enable()` zijn SECURITY DEFINER en aanroepbaar door
  anon/authenticated via RPC.* Dit horen trigger-helpers te zijn, geen publieke RPC.
  → `REVOKE EXECUTE ... FROM anon, authenticated;` (of SECURITY INVOKER maken).
- *`handle_updated_at()` heeft mutable search_path* → `SET search_path = ''` toevoegen (hardening
  tegen search_path-hijack).

**S4. Geen HTTP security headers (zeer laag voor een loopback-app).**
CSP / X-Frame-Options / nosniff ontbreken. Voor een lokale single-page app weinig impact, maar
X-Frame-Options + nosniff zijn gratis meegenomen in dezelfde `before_request` als S1.

> Niet gevonden (goed nieuws): geen exposed service_role, geen RLS-gat, geen self-upgrade,
> geen open CORS, geen injection. De grote 4 vibecode-killers zijn allemaal afwezig.

---

## DEEL 4 — Voorgestelde volgorde (na jouw akkoord)

**Nu meteen, zonder rebuild:**
1. Login bevestigen via account B/C (DEEL 1). Bevestigt dat ffmpeg+auth+upload werken.
2. Admin-wachtwoord netjes zetten/resetten.

**Kleine code-fixes (1 rebuild samen):**
3. `_ffmpeg_has_drawtext` patroon verruimen (DEEL 2). → captions terug.
4. Host-header/Origin-check + nosniff/X-Frame-Options als `before_request` (S1 + S4).
5. Home-whitelist op `/api/upload-local` (S2).
6. `git commit` (media_tools.py, app.py, cutter.py, build_macos.sh, .gitignore, static/index.html
   + nieuwe fixes), dan `./build_macos.sh sign notarize dmg`, DMG vervangen op
   `downloads.omnidj.com`.

**Supabase (los van rebuild, dashboard + 1 SQL-migratie):**
7. Leaked Password Protection aanzetten.
8. `REVOKE EXECUTE` op de 2 SECURITY DEFINER-functies + `search_path` fix (S3).

**Daarna:**
9. Smoke-test op een 2e Mac (download via URL, geen Gatekeeper-popup, login, upload, export
   met captions).

---

## Bronnen (security-research)
- Supabase RLS / anon vs service_role valkuilen: https://www.stingrai.io/blog/supabase-powerful-but-one-misconfiguration-away-from-disaster
- Lovable/Supabase RLS-lek (170+ apps, CVE-2025-48757): https://www.superblocks.com/blog/lovable-vulnerabilities
- Localhost CORS + DNS-rebinding: https://github.blog/security/application-security/localhost-dangers-cors-and-dns-rebinding/
- Vibe-coding security-risico's overzicht: https://getautonoma.com/blog/vibe-coding-security-risks
