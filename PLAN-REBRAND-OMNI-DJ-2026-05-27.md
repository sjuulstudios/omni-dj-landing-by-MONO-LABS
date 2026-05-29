# PLAN — Rebrand naar Omni DJ (MONO LABS)

> **Datum opgesteld:** 2026-05-27 (sessie post-52)
> **Update:** 2026-05-28 (sessie 59+) — Sjuul heeft de folder-renames al uitgevoerd in Finder. Sectie 4 + 8 zijn daardoor grotendeels al gedaan. Code-rebrand + .app rebuild + externe services + email-templates + DNS staan nog open.
> **Status:** PLAN — niet uitvoeren. Bevat volledige breakdown + runbook.
> **Strategie:** Big bang. Code, services, domein, branding in één sessie.
> **Geen users:** Geen migratie-zorgen. Stripe customers + Supabase auth-users zijn er nog niet, alleen Sjuul's eigen test-accounts.
>
> **Huidige paden (na sessie 59):**
> - Project-root: `/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/`
> - Subfolder (Python source): `/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/Omni DJ/`
> - Test-sets folder: `/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/Omni DJ/OMNI DJ - TEST DJ-SETS/`

---

## 0. Beslissingen die de basis van dit plan zijn

Alles hieronder is bevestigd door Sjuul op 2026-05-27. Als één hiervan verandert, moet het plan opnieuw.

| Onderwerp | Beslissing |
|---|---|
| Timing | Big bang — alles in één sessie |
| Beta-users / data | Geen users, dus Stripe + Supabase project **behouden** (alleen renamen) |
| Oude naam | Volledig verwijderen — alle varianten (Clip Live, Clipdrop, Clip Drop, Clipdrop Live, Clip Drop Live, DJClips, djclips.nl, clipdroplive.com, clipdrop.com) |
| Project-folder | **Al gedaan in sessie 59:** `/Clip Live/` → `/Omni DJ/` en `/dj-clip-cutter/` → `/Omni DJ/` (twee keer Omni DJ — Sjuul koos title-case ipv kebab-case) |
| Product-naam | **Omni DJ** (title case — niet "OMNI DJ" all-caps, niet "OmniDJ" PascalCase) |
| Code/folders/env-vars | `omni-dj` / `omnidj` / `OMNI_DJ` (kebab-case lowercase, soms upper voor env) |
| Domein | `omni.com` (geen subdomein, geen 'dj' in URL) |
| MONO LABS-zichtbaarheid | Subtiel in footer/legal, plus klein "Omni DJ by MONO LABS"-element bovenin app/website |
| Visual identity | Voorlopig huidige stijl behouden — alleen tekst-rebrand. Sub-task voor latere visual-refresh. |
| .app-bundle | Hernoemen naar `Omni DJ.app` + nieuwe Bundle ID `com.monolabs.omnidj`. Oude .app uit `/Applications` verwijderen. |
| Cloudflare | Domein gekocht, Cloudflare nog niet ingesteld. Plan bevat volledige setup. |
| Externe services in scope | Stripe + Supabase + Cloudflare + Gmail/Workspace mail-routing |
| Marketing/launch | OUT OF SCOPE — puur technisch plan. Beta-flyer/uitnodiging-mail blijft uit scope per [[feedback_beta_flyer_skip]]. |
| Admin-emails | `omnidj@monohq-labs.com` (system FROM-adres) + `sjuul@monohq-labs.com` (jouw eigen admin-account) — beide unlimited via `profiles.role='admin'` + `plan='studio'`. |

---

## 1. Wat we tegenkwamen — naam-archeologie

De codebase bevat **vijf verschillende oude merknamen**, soms door elkaar in hetzelfde bestand. Belangrijk om te kennen voordat je gaat search-and-replacen — anders mis je varianten.

| Variant | Waar gevonden | Aantal hits (ruw) |
|---|---|---|
| `Clip Live` | App-titel, HANDOVER, plannen, build-script, .app-bundle naam | ~500 |
| `cliplive` / `ClipLive` | Bundle ID `com.sjuulstudios.cliplive`, env-var prefix `CLIP_LIVE_*`, PyInstaller spec, localStorage keys `clipLive.*`, feature-flag `clipLiveRedesignV2` | ~150 |
| `Clip Drop` / `Clipdrop` | Supabase migrations comment, oude folder `CLIP DROP DJ-SETS`, project-naam in Supabase = "Clip Drop Live" | ~50 |
| `Clipdrop Live` / `clipdroplive.com` | Landing-pagina (`landing/index.html` titel, og:url, canonical), oud productie-domein | ~30 |
| `DJClips` / `djclips.nl` | Beoogd productie-domein, GitHub repo `sjuulstudios/djclips.nl-by-MONO-LABS`, reset-password footer, oude wachtwoord-blacklist | ~75 |
| `Sjuul Studios` / `sjuulstudios` | Copyright, Apple Developer ID, Apple ID `business@sjuulstudios.com`, KvK/VAT context in Stripe webhook | ~40 |

**Totaal:** ±900 occurrences over 71 files.

**Eén "MONO LABS"-referentie bestaat al** in oude GitHub repo-naam (`djclips.nl-by-MONO-LABS`) en in oude HANDOVER (`.backups/HANDOVER-pre-compact-2026-05-26.md`). Goede aanwijzing voor consistente spelling = "MONO LABS" met spatie + caps.

---

## 2. Naamgebruiks-spelregels (definitief)

Deze tabel is de bron-van-waarheid voor search-and-replace. Hou je hieraan, anders krijg je gemengde spellingen.

| Context | Voor | Na |
|---|---|---|
| Product-naam in UI / marketing / docs / titles | Clip Live, Clipdrop Live, Clip Drop Live, Clipdrop | **Omni DJ** |
| Product-naam in zinnen ("the Clip Live app") | "Clip Live", "the Clip Live app" | "Omni DJ" |
| All-caps mention | CLIP LIVE | **OMNI DJ** (alleen in headings die nu al all-caps zijn) |
| Bedrijfsnaam | Sjuul Studios | **MONO LABS** |
| Footer-attributie | "© 2026 Sjuul Studios" | **"© 2026 MONO LABS"** |
| Tagline-vorm | "Clip Live" alleen | **"Omni DJ by MONO LABS"** (in top-nav + footer + about) |
| Code-folders | `dj-clip-cutter`, `Clip Live`, `CLIP DROP DJ-SETS` | **`Omni DJ`** (subfolder), `Omni DJ` (workspace-root), `OMNI DJ - TEST DJ-SETS` (sessie 59 actual rename) |
| Bundle ID | `com.sjuulstudios.cliplive` | **`com.monolabs.omnidj`** |
| .app file | `Clip Live.app` | **`Omni DJ.app`** |
| .dmg file | `Clip Live.dmg` | **`Omni DJ.dmg`** |
| Env-vars | `CLIP_LIVE_USER_DATA`, `CLIP_LIVE_PORT`, `CLIP_LIVE_BIND` | **`OMNI_DJ_USER_DATA`**, **`OMNI_DJ_PORT`**, **`OMNI_DJ_BIND`** |
| localStorage keys | `clipLive.session`, `clipLive.activeJobId`, `clipLive.trim.*`, `clipLive.exportDir`, `clipLive.exportSettings`, `clipLive.lastExportDir`, `clipLive.wizardState`, `cliplive.brandstack.collapsed.v1`, `clipLiveRedesignV2` | **`omniDj.session`**, **`omniDj.activeJobId`**, **`omniDj.trim.*`**, **`omniDj.exportDir`**, **`omniDj.exportSettings`**, **`omniDj.lastExportDir`**, **`omniDj.wizardState`**, **`omniDj.brandstack.collapsed.v1`**, **`omniDjRedesignV2`** |
| macOS user-data folder | `~/Library/Application Support/Clip Live` | **`~/Library/Application Support/Omni DJ`** |
| Windows user-data | `%APPDATA%\Clip Live` | **`%APPDATA%\Omni DJ`** |
| Linux user-data | `~/.clip-live` | **`~/.omni-dj`** |
| Domain | clipdroplive.com, djclips.nl | **omni.com** |
| Marketing-email (FROM) | business@sjuulstudios.com | **omnidj@monohq-labs.com** |
| Sjuul's persoonlijk admin-account | business@sjuulstudios.com (test) | **sjuul@monohq-labs.com** |
| Apple Notary keychain profile | `cliplive-notary` | **`omnidj-notary`** |
| Stripe product-namen | "Clip Live — Pro" / "Clip Live — Studio" | **"Omni DJ — Pro"** / **"Omni DJ — Studio"** |
| Stripe webhook URL (referentie) | (test-mode op huidige Supabase) | blijft hetzelfde Supabase-project, alleen rename |
| Supabase project display-name | "Clip Drop Live" | **"Omni DJ"** |
| Supabase password-reset redirect | `http://127.0.0.1:5555/static/reset-password.html` (lokaal) + `https://djclips.nl/reset-password` (geweest) | lokaal blijft, productie wordt **`https://omni.com/reset-password`** |
| GitHub repo (landing) | `sjuulstudios/djclips.nl-by-MONO-LABS` | **`monolabs/omni-dj-landing`** (of vergelijkbaar — zie sectie 9) |

### Edge-cases die search-and-replace mist

- **`cliplive` in losse `.spec` strings, build-script (`cliplive_dmg_settings.py`, `cliplive_restart.log`), tracking.py (`cliplive-track-`), test_quota.sh prefix** — case-sensitive search nodig.
- **Wachtwoord-blacklist in `auth.py:418`** bevat `'clipdrop1'`, `'clipdrop123'`, `'djclips01'`, `'djclips123'` — vervangen door `'omnidj1'`, `'omnidj123'`, `'omni1'`, `'omni123'`.
- **Comments in oude .bak-backups** — die negeren we (zie sectie 7).
- **HANDOVER session-log markers** als `SESSIE 51 fix` blijven — zijn historische verwijzingen naar code-commits, geen brand.

---

## 3. File-by-file breakdown

Volledige lijst van wat in elk bestand gewijzigd moet worden. Geen volledige diff — je voert later sed/Edit uit aan de hand van deze checklist.

> **Pad-conventie in de tabellen hieronder:** De prefix `dj-clip-cutter/` is historisch (sessie 59 hernoemde dit naar `Omni DJ/`). In praktijk dus: lees `dj-clip-cutter/app.py` als `Omni DJ/app.py` (sub-folder van project-root). Het bestaan en hits-aantal per file kloppen nog, alleen de pad-prefix is veranderd. Voor sed-doeleinden is dit irrelevant — de find draait recursief vanaf project-root.

### 3.1 Python source — kritisch pad

| File | Hits | Wat moet veranderen |
|---|---|---|
| `dj-clip-cutter/app.py` | 13 + 7 | Comment-strings, `CLIP_LIVE_USER_DATA` → `OMNI_DJ_USER_DATA` (incl. de fallback-check op regel 187/1397), `CLIP_LIVE_BIND`/`CLIP_LIVE_PORT` env-vars, alle `Clip Live`-mentions in docstrings + log-messages. Let op: de env-var-rename moet **gecoordineerd** met `launcher.py`. |
| `dj-clip-cutter/launcher.py` | 4 + 2 | `Clip Live` mentions in docstring/folder-pad (`Library/Application Support/Clip Live` → `Omni DJ`), `APPDATA/Clip Live` → `Omni DJ`, `~/.clip-live` → `~/.omni-dj`, `os.environ.setdefault("CLIP_LIVE_USER_DATA"...)` → `OMNI_DJ_USER_DATA`, `os.environ.get("CLIP_LIVE_PORT")` → `OMNI_DJ_PORT`. |
| `dj-clip-cutter/cutter.py` | 1 + 1 | `CLIP_LIVE_USER_DATA` op regel 847 (fallback-rij in env-var-zoeklijst) → `OMNI_DJ_USER_DATA`. Cliplive-mention checken. |
| `dj-clip-cutter/auth.py` | 4 + 2 | Comments + redirect-URL hint (`djclips.nl`), wachtwoord-blacklist `clipdrop1/clipdrop123/djclips01/djclips123` → `omnidj1/omnidj123/omni1/omni123`. |
| `dj-clip-cutter/billing.py` | 3 | "Clip Live" comments, Sjuul Studios-vermelding indien aanwezig. |
| `dj-clip-cutter/runtime_config.py` | 1 | Docstring "Clip Live — runtime configuration" → "Omni DJ — runtime configuration". Keys blijven (Supabase URL etc.). |
| `dj-clip-cutter/uploader.py` | 1 | Comment-strings. |
| `dj-clip-cutter/spectrogram.py` | 1 | Comment. |
| `dj-clip-cutter/watch_folder.py` | 1 | Comment. |
| `dj-clip-cutter/tracking.py` | 1 | `tempfile.TemporaryDirectory(prefix='cliplive-track-')` → `prefix='omnidj-track-'`. |
| `dj-clip-cutter/launcher.py` log-prefix | — | `launcher.log` filename blijft (per-user data dir wordt al door rename gevangen). |
| `dj-clip-cutter/test_export_settings.py` | 2 | Comments / hard-coded paths. |

### 3.2 Frontend / HTML / JS

| File | Hits | Wat moet veranderen |
|---|---|---|
| `dj-clip-cutter/static/index.html` | 43 + 2 + 16 localStorage | `<title>Clip Live</title>` → `Omni DJ`, alle visible "Clip Live"-strings, **alle localStorage-keys** (zie sectie 2 — 9 keys totaal), `clipLiveRedesignV2` feature-flag, FLAG_KEY constant. Watch-out: `body.redesign-v2` blijft (CSS klasse, niet brand). Footer "by MONO LABS" toevoegen. |
| `dj-clip-cutter/static/reset-password.html` | 7 | Title, body-text "Clip Live", footer `Clip Live · djclips.nl` → `Omni DJ · omni.com`, "Terug naar Clip Live"-knop tekst. Plus localStorage-key `clipLive.session` → `omniDj.session`. |
| `landing/index.html` | 17 | **Volledige rebrand**: title "Clipdrop Live - Detect drops..." → "Omni DJ - ...", meta-description, og:title, og:url `clipdroplive.com` → `omni.com`, og:image-URL, canonical, twitter:image, brand-name span, hero-text "Clipdrop Live finds the drops", alle button labels die de naam noemen. |
| `landing/terms.html` | 15 | Brand-name + entity-naam (Sjuul Studios → MONO LABS). |
| `landing/privacy.html` | 14 | Brand-name + entity-naam + Data Controller info. |
| `landing/contact.html` | 5 | Brand-name + contact-email `business@sjuulstudios.com` → `omnidj@monohq-labs.com`. |
| `landing/README.md` | 16 | Repo-docs. |
| `landing/script.js` | 1 | Brand-mention in comment of analytics-tag. |
| `landing/styles.css` | 2 | Comments. |
| `landing/sitemap.xml` | 4 | URLs `https://clipdroplive.com/...` → `https://omni.com/...`. |
| `landing/robots.txt` | 1 | Sitemap-URL. |
| `landing/og-image.svg` | 1 | SVG bevat de brand-text "Clipdrop Live" — moet "Omni DJ" worden (of nieuwe SVG genereren). |
| `landing/favicon.svg` | 0 hits maar | Visueel checken: huidig favicon is mogelijk gestileerde "C" — als dat zo is, vervangen door simpele "O" of MONO LABS-mark. Sub-task voor visual-refresh. |
| `landing/vercel.json` | 0 (verwacht) | Check redirects / headers — moet niks oud-domein staan. |

### 3.3 Build / PyInstaller / shell-scripts

| File | Hits | Wat moet veranderen |
|---|---|---|
| `dj-clip-cutter/ClipLive.spec` (→ rename naar `OmniDJ.spec`) | 14 | Docstring, `bundle_identifier="com.sjuulstudios.cliplive"` → `com.monolabs.omnidj`, `name="Clip Live"` (3x in EXE/COLLECT/BUNDLE), `Clip Live.app`, `CFBundleName`/`CFBundleDisplayName`, copyright `© 2026 Sjuul Studios` → `© 2026 MONO LABS`, alle `NS*UsageDescription` strings die "Clip Live" noemen → "Omni DJ". |
| `dj-clip-cutter/build_macos.sh` | 23 | Header-comment, `pyinstaller --noconfirm ClipLive.spec` → `OmniDJ.spec`, alle `dist/Clip Live.app` paden → `dist/Omni DJ.app`, `cliplive-launch.sh` interne wrapper → `omni-dj-launch.sh`, notary-profile-naam `cliplive-notary` → `omnidj-notary`, Apple ID `business@sjuulstudios.com` → `omnidj@monohq-labs.com` (LET OP: dit is alleen het voorbeeld in de help-tekst. Echte Apple Developer-account is een aparte vraag — zie OPEN VRAGEN). DMG-settings tempfile `cliplive_dmg_settings.py` → `omnidj_dmg_settings.py`. Final `dmgbuild ... "Clip Live" "dist/Clip Live.dmg"` → `"Omni DJ" "dist/Omni DJ.dmg"`. |
| `dj-clip-cutter/entitlements.plist` | 1 | Identifier-references als die in de plist staan. |
| `dj-clip-cutter/start.sh` | 0 (mogelijk) | Header-comment, `cd "/Users/sjuulsmits/Documents/Claude/Projects/Clip Live/dj-clip-cutter"` → nieuwe pad `/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/Omni DJ/`. |
| `dj-clip-cutter/_restart.sh` | 1 | `/tmp/cliplive_restart.log` → `/tmp/omnidj_restart.log`. |
| `dj-clip-cutter/test_auth.sh` | 1 | Test-email `business+cliptest@sjuulstudios.com` → `omnidj+test@monohq-labs.com` (of nieuwe test-mailbox — zie sectie 5). |
| `dj-clip-cutter/test_quota.sh` | 1 | Idem. |
| `dj-clip-cutter/scripts/set-stripe-secrets.sh` | 2 | Header-comment + werkdirectory-pad. |
| `dj-clip-cutter/scripts/cleanup_legacy_jobs.py` | 6 | Brand-mentions + pad-defaults. |
| `init_git.sh` (root) | 8 | Repo-naam, remote-URL. |
| `cleanup_bak_files.sh` (root) | 3 | Comments. |

### 3.4 Supabase functions + migrations

Edge functions zelf draaien in Deno op Supabase — alleen comments updaten (geen functioneel verschil). Maar de **deploy-paden** in de docstrings noemen het oude project-pad.

| File | Hits | Wat moet veranderen |
|---|---|---|
| `dj-clip-cutter/supabase/functions/create-checkout-session/index.ts` | 2 | Comments "Clip Live desktop-app" → "Omni DJ desktop-app", deploy-pad in docstring. **Sjuul Studios-mention** rond Stripe Tax. |
| `dj-clip-cutter/supabase/functions/create-portal-session/index.ts` | 1 | Idem + "Sjuul Studios". |
| `dj-clip-cutter/supabase/functions/stripe-webhook/index.ts` | 1 | Idem. |
| `dj-clip-cutter/supabase/functions/stripe-webhook/README.md` | 3 | Comments. |
| `dj-clip-cutter/supabase/functions/update-usage/index.ts` | 2 | Comments. |
| `dj-clip-cutter/supabase/migrations/001_rls_policies.sql` | 1 | Header-comment "Clip Live / Clip Drop" → "Omni DJ". |
| `dj-clip-cutter/supabase/migrations/002_audit_logs.sql` | 1 | Idem. |
| `dj-clip-cutter/supabase/migrations/003_rbac_role_column.sql` | 1 | Idem. |
| `dj-clip-cutter/supabase/migrations/README.md` | 3 | Idem. |
| `dj-clip-cutter/supabase/.temp/linked-project.json` | 1 | `"name":"Clip Drop Live"` → `"name":"Omni DJ"`. Wordt ook bijgewerkt zodra je in dashboard rename doet (deze JSON wordt gegenereerd door `supabase link`). |

### 3.5 Documentatie / .md-bestanden

Per Sjuul's beslissing: **alle .md-bestanden hernoemen + interne refs updaten** (inclusief ARCHIVE).

| File | Hits | Actie |
|---|---|---|
| `.claude/CLAUDE.md` | 5 | Volledige rewrite — projectnaam, paden, app-titel, app-starten-instructies. |
| `HANDOVER.md` | 62 | Rewrite: title, alle session-summary bullets die "Clip Live" zeggen, paden, `.app`-naam. |
| `HANDOVER-ARCHIVE.md` | 51 | Idem. |
| `LESSONS-LEARNED.md` | 18 | Idem. |
| `INSTALL.md` | 12 | App-naam + paden + commando's. |
| `INSTALLER-RUNBOOK.md` | 20 | Bundle-naam, paden, Apple-cert references. |
| `QUICK-REFERENCE.md` | 9 | Terminal-cheatsheet — paden + start-commando. |
| `MOCKUP-EXTRACTION.md` | 3 | References. |
| `PLAN-CONTENT-CALENDAR-2026-05-26.md` | 25 + 11 djclips | Volledige rewrite (referenties naar djclips.nl, Clip Live, MONO LABS). |
| `PLAN-MOAT-FEATURES-2026-05-26.md` | 17 | Idem. |
| `PLAN-REDESIGN-2026-05-26.md` | 3 | Idem. |
| `PLAN-REDESIGN-MIGRATION-2026-05-26.md` | 4 | Idem. |
| `SESSIE-1-PLAN.md` | 4 | Idem. |
| `SESSIE-24-FINDINGS.md` | 3 | Idem. |
| `SESSIE-31-START-PROMPT.md` | 1 | Idem. |
| `SESSIE-46-START-PROMPT.md` | 7 | Idem. |
| `SESSIE30-REBUILD-RUNBOOK.md` | 9 | Idem. |
| `SESSIE31-REBUILD-RUNBOOK.md` | 10 | Idem. |
| `SESSIE33-RECUT-QUEUE-PLAN.md` | 0 (te checken) | Idem. |
| `SESSIE34-CAPTION-FONTS-PLAN.md` | 3 | Idem. |
| `SESSIE34-PASSWORD-RESET-PLAN.md` | 15 + 10 djclips | Hardcoded `djclips.nl` URLs + email-template footer "Clipdrop · djclips.nl" → "Omni DJ · omni.com". |
| `SESSIE43-EXPORT-PIPELINE-PLAN.md` | 1 | Idem. |
| `SESSIE48-REBUILD-RUNBOOK.md` | 18 | Bundle-naam + .dmg-naam + paden. |
| `STRIPE-DNS-RUNBOOK.md` | 15 + 7 djclips | Hele runbook praat over "Clip Live", `cliplive.app` als beoogd domein, Sjuul Studios. Volledige rewrite of vervangen door nieuwe Omni DJ-versie. |
| `dj-clip-cutter/SESSIE35-NATIVE-PICKER-PLAN.md` | 9 + 1 | Idem. |
| `dj-clip-cutter/VIDEO_EDITOR_PLAN.md` | 1 | Idem. |
| `landing/README.md` | 16 | Repo-docs. |

### 3.6 Project-root / overige

| File | Hits | Actie |
|---|---|---|
| `.gitignore` (root) | 1 | Mogelijke comment of pattern met oude naam. |
| `clip-live-redesign.html` (root, mockup) | 5 | **Hernoemen** naar `omni-dj-redesign.html` (of behouden als historisch — Sjuul kiest). |
| `clip-live-redesign-v2.html` (root, mockup) | 5 | Idem → `omni-dj-redesign-v2.html`. |
| `clip-drop-financial-dashboard.html` (root) | 2 | Hernoemen + branding. |
| `business-model-2026/CLIP-LIVE-BUSINESS-MODEL-PLAN.docx` | n/a (binary) | Hernoemen naar `OMNI-DJ-BUSINESS-MODEL-PLAN.docx`. Interne inhoud handmatig updaten (binary — geen sed). |
| `business-model-2026/CLIP-LIVE-FINANCIEEL-MODEL.xlsx` | n/a (binary) | Hernoemen naar `OMNI-DJ-FINANCIEEL-MODEL.xlsx`. Interne sheets handmatig. |

### 3.7 Bestanden die **bewust ongemoeid** blijven

- **Alle `.bak` / `.backup-*` bestanden** — zijn historische snapshots, niet leesbaar voor gebruikers, geen production-impact. Eventueel later weggooien met `cleanup_bak_files.sh`.
- **`.git/` directory** — git-history niet rewriten. Commits behouden hun originele berichten. Reden: rewriting history breekt eventuele clones + remote.
- **`venv/`** — Python virtual environment, wordt opnieuw gegenereerd.
- **`__pycache__/`** — bytecode cache, wordt opnieuw gegenereerd.
- **`build/` en `dist/`** — PyInstaller output, wordt opnieuw gegenereerd na rebuild.
- **`yolov8n.pt`** — model-bestand, geen brand-reference.
- **`system_fonts_cache.json`** — fonts-cache, geen brand-reference.

---

## 4. Folder-rename runbook (lokale Mac)

> **UPDATE 2026-05-28 (sessie 59) — DEZE SECTIE IS GROTENDEELS AL UITGEVOERD.** Sjuul heeft op 28 mei handmatig in Finder drie folders hernoemd. Belangrijk verschil met dit plan: Sjuul koos voor **`Omni DJ/Omni DJ/`** (twee keer Omni DJ, sub-folder gelijk aan root-naam) in plaats van het oorspronkelijk geplande `Omni DJ/omni-dj/` (kebab-case subfolder).
>
> **Wat al gedaan is in sessie 59:**
> - ✅ Root folder: `/Clip Live/` → `/Omni DJ/`
> - ✅ Subfolder: `Clip Live/dj-clip-cutter/` → `Omni DJ/Omni DJ/`
> - ✅ Test-sets folder: `CLIP DROP DJ-SETS/` → `OMNI DJ - TEST DJ-SETS/`
> - ✅ Live code-paden gepatcht (zie sessie 59 HANDOVER): `build_sess53.sh`, `test_export_settings.py`, `cleanup_legacy_jobs.py`, 4× supabase functions deploy-headers, `stripe-webhook/README.md`, `static/index.html` placeholders.
> - ✅ Claude's cowork-mount wijst naar `/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/`.
>
> **Wat nog moet (in big-bang rebrand-sessie):**
> - ❌ Backup van project (tar.gz) — sectie 4.1 hieronder, doe alsnog vóór de sed-rebrand begint
> - ❌ Oude `Clip Live.app` uit `/Applications` verwijderen
> - ❌ Sjuul's terminal-alias updaten naar `cd "~/Documents/Claude/Projects/Omni DJ/Omni DJ"` (twee keer Omni DJ)
> - ❌ Oude `~/Library/Application Support/Clip Live/` user-data weggooien
> - ❌ Alle resterende `Clip Live`-mentions in code/UI/docs scrubben (zie sectie 7)
>
> **Consequenties voor de rest van dit plan:**
> - In de pad-tabellen en sed-commando's hieronder is `dj-clip-cutter/` → `Omni DJ/` (de sub-folder), niet `omni-dj/` zoals oorspronkelijk gepland
> - Sectie 8 (folder-renames) wordt overgeslagen (al gedaan) — alleen de mockup-/business-doc-renames in 8c-8d nog uitvoeren

### 4.1 Resterende pre-flight stappen (voor de big-bang sessie)

1. **Backup eerst** (full project tar.gz buiten de folder):
   ```bash
   cd ~/Documents/Claude/Projects
   tar -czf omni-dj-pre-rebrand-$(date +%Y%m%d).tar.gz "Omni DJ"
   ```
2. **Sluit alles wat naar het project wijst:**
   - Stop dev-server (Cmd+Tab Terminal → Ctrl+C, of `lsof -nP -iTCP:5555 -sTCP:LISTEN` → kill PID).
   - Quit `Clip Live.app` als die draait (Cmd+Q).
   - Quit alle editors (VS Code, Sublime, etc.) die de folder open hebben.
3. **Verwijder oude `.app` uit `/Applications`:**
   ```bash
   rm -rf "/Applications/Clip Live.app"
   ```
4. **Verwijder oude user-data folder** (geen users, dus niks belangrijks):
   ```bash
   rm -rf ~/Library/Application\ Support/Clip\ Live
   ```
5. **Code-side rebrand UITVOEREN** (sectie 7).
6. **Verifieer** dev-server na rebrand:
   ```bash
   cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/Omni DJ"
   ./start.sh
   ```
   App moet op `127.0.0.1:5555` opstarten zonder errors. Tab-title = "Omni DJ".

### 4.2 Wat breekt door folder-rename (en hoe te fixen) — historische context

| Wat | Waar | Fix |
|---|---|---|
| `start.sh` cd-commando | `start.sh` regel 1 | Path zelf is relatief (`cd "$(dirname "$0")"` of vergelijkbaar) — werkt ongeacht naam. Maar als hij absoluut pad heeft: aanpassen. |
| Sjuul's terminal-shortcut | `~/.zshrc` of een alias | Sjuul moet zijn alias updaten van `cd "~/Documents/Claude/Projects/Clip Live/dj-clip-cutter"` naar `cd "~/Documents/Claude/Projects/Omni DJ/Omni DJ"` (twee keer Omni DJ). |
| HANDOVER-cd-instructies | `HANDOVER.md`, `QUICK-REFERENCE.md`, alle SESSIE-RUNBOOK.md | Already in scope sectie 3.5. |
| Supabase CLI link-state | `dj-clip-cutter/supabase/.temp/linked-project.json` | Wordt opnieuw gegenereerd bij volgende `supabase link`. Of handmatig pad-onafhankelijk maken. |
| `~/Library/Application Support/Clip Live/` (user-data) | macOS gebruikers-folder | Niet renamen — wordt opnieuw aangemaakt door nieuwe launcher.py als `Omni DJ`. **Geen users, dus geen migratie van job_history nodig.** Wel: handmatig oude folder weggooien als clean-up: `rm -rf ~/Library/Application\ Support/Clip\ Live`. |

---

## 5. Externe services — stap-voor-stap

### 5.1 Supabase — project renamen + email-templates

Het Supabase-project blijft hetzelfde (ref: `lbabsffxefkrxwzkbzar`). Alleen rename + email-templates + redirect-URLs.

#### Stap 1 — Project display-name renamen

1. Log in op https://supabase.com/dashboard
2. Selecteer project "Clip Drop Live" (ref `lbabsffxefkrxwzkbzar`)
3. Linker sidebar onderaan: **Settings** (tandwiel-icoon)
4. Eerste tab: **General**
5. Bovenaan: **Project Name** veld → wijzig van `Clip Drop Live` naar **`Omni DJ`**
6. Klik **Save** rechtsonder
7. **Verifieer:** ververs pagina → projectnaam links bovenin staat als "Omni DJ"

#### Stap 2 — Auth Email Templates updaten

Supabase mailt automatisch bij signup + password-reset. Templates verwijzen waarschijnlijk impliciet naar de oude naam.

1. **Authentication** (linker sidebar) → **Email Templates**
2. Per template (er zijn er ~4: Confirm signup, Magic Link, Change Email Address, Reset Password) klik **Customize**
3. Vervang in subject + HTML body alle voorkomens van:
   - `Clip Drop Live` → `Omni DJ`
   - `Clip Live` → `Omni DJ`
   - Footer-mention `Sjuul Studios` → `MONO LABS`
   - URLs `djclips.nl` of `clipdroplive.com` → `omni.com`
4. **Save** per template

**Template-tekst voorbeeld voor "Reset Password" (vervang volledig):**
```html
<h2>Wachtwoord resetten — Omni DJ</h2>
<p>Klik op de onderstaande link om je wachtwoord te resetten. De link is 1 uur geldig.</p>
<p><a href="{{ .ConfirmationURL }}">Reset wachtwoord</a></p>
<p style="color:#888;font-size:12px;margin-top:24px">
  Omni DJ · <a href="https://omni.com">omni.com</a><br/>
  Heb je dit niet aangevraagd? Negeer deze mail.
</p>
```

#### Stap 3 — URL-Allowlist updaten

1. **Authentication** → **URL Configuration**
2. **Site URL:** `http://127.0.0.1:5555` (laat lokaal, voor dev) — voeg later `https://omni.com` toe als productie-URL
3. **Redirect URLs (allowlist):**
   - Houden: `http://127.0.0.1:5555/static/reset-password.html`
   - Verwijderen: `https://djclips.nl/reset-password` (als die er staat)
   - Toevoegen: `https://omni.com/reset-password`
   - Toevoegen: `https://omni.com/auth/callback` (voor toekomstige OAuth)
4. **Save**

#### Stap 4 — Auth-FROM-adres customizen (SMTP)

Standaard mailt Supabase vanuit `noreply@mail.app.supabase.io`. Voor MONO LABS-branding moet je een custom SMTP koppelen.

**Optie A (snelste, gratis voor lage volumes):** Gebruik Gmail SMTP voor `omnidj@monohq-labs.com`.

1. **Project Settings** → **Authentication** → **SMTP Settings** (scroll naar beneden)
2. Toggle **Enable Custom SMTP** aan
3. Vul in:
   - **Sender email:** `omnidj@monohq-labs.com`
   - **Sender name:** `Omni DJ`
   - **Host:** `smtp.gmail.com`
   - **Port:** `587`
   - **Username:** `omnidj@monohq-labs.com`
   - **Password:** een **App Password** van Google (NIET je gewone wachtwoord — moet via myaccount.google.com → Security → App passwords)
   - **Encryption:** STARTTLS
4. **Save**
5. **Verifieer** door zelf een password-reset aan te vragen met een test-email en kijken of mail vanuit `omnidj@monohq-labs.com` arriveert.

**Optie B (productie, $20/mo):** Resend.com — bouwt voor jou DKIM/SPF, hoger leverbaarheids-score. Voor nu Optie A; later upgrade.

#### Stap 5 — Admin-emails whitelisten (unlimited access)

In code is geen email-allowlist. Alles loopt via `profiles.role` ∈ {'user','beta','admin'} + `profiles.plan` ∈ {'free','pro','studio'}. Voor unlimited access geef je beide admin-emails `role='admin'` + `plan='studio'`.

**Stappen — pas uit te voeren ná je de twee accounts hebt aangemaakt via de normale signup-flow:**

1. **SQL Editor** in Supabase Dashboard → **+ New query**
2. Plak (en pas eventueel de stripe_customer_id-velden aan — die mogen leeg blijven):
   ```sql
   -- Whitelist beide admin-emails: rol=admin + plan=studio + onbeperkte quota
   UPDATE public.profiles
   SET
     role = 'admin',
     plan = 'studio',
     usage_this_period = 0
   WHERE email IN ('omnidj@monohq-labs.com', 'sjuul@monohq-labs.com');

   -- Verifieer:
   SELECT id, email, role, plan, usage_this_period
   FROM public.profiles
   WHERE email IN ('omnidj@monohq-labs.com', 'sjuul@monohq-labs.com');
   ```
3. **Run** — output moet 2 rijen tonen, beide met `role='admin'`, `plan='studio'`.

**Belangrijk:** de profiles-rij wordt pas aangemaakt zodra de gebruiker een keer is ingelogd (trigger op auth.users → profiles). Dus eerst:
1. Sign up `omnidj@monohq-labs.com` via app
2. Sign up `sjuul@monohq-labs.com` via app
3. Dan bovenstaande SQL draaien

### 5.2 Stripe — products renamen + (later) domein

Stripe-product-IDs blijven hetzelfde (`price_1TUoYNA5DKhJaSAF6xynooY9` voor Pro, `price_1TUoZCA5DKhJaSAFI7AMgAbA` voor Studio). Alleen de display-namen + business profile aanpassen.

#### Stap 1 — Account display-name + brand

1. Log in op https://dashboard.stripe.com (zorg dat je in TEST-mode bent — toggle linksonder)
2. **Settings** (tandwiel rechtsboven) → **Business settings** → **Public details**
3. Pas aan:
   - **Statement descriptor:** `OMNI DJ` (max 22 chars, wordt op bankafschrift getoond)
   - **Public business name:** `Omni DJ`
   - **Public phone / website:** website → `https://omni.com`
   - **Support email:** `omnidj@monohq-labs.com`
4. **Save**
5. **Settings** → **Business settings** → **Branding**
6. Upload: nieuw logo (voorlopig kun je het MONO LABS-logo gebruiken óf een placeholder Omni DJ-text-logo). Pas brand color aan naar accent-oranje (`#D97742` uit de v2-redesign) of de definitieve Omni DJ-kleur als die er is.
7. **Save**

#### Stap 2 — Products + Prices renamen

1. **Products** → klik op `Clip Live — Pro` (of vergelijkbare oude naam)
2. Klik **Edit product**
3. **Name:** `Clip Live — Pro` → **`Omni DJ — Pro`**
4. **Description:** vervang elke "Clip Live"-mention door "Omni DJ"
5. **Save**
6. Herhaal voor `Clip Live — Studio` → `Omni DJ — Studio`
7. **Verifieer:** Products-lijst toont nu beide nieuwe namen
8. **Price IDs blijven gelijk** — geen verdere actie in code nodig

#### Stap 3 — Webhook endpoint (alleen URL refresheren als webhook al gedeployd was)

Webhook URL is `https://lbabsffxefkrxwzkbzar.supabase.co/functions/v1/stripe-webhook` — die blijft hetzelfde want we behouden het Supabase-project.

Geen actie nodig.

#### Stap 4 — Customer Portal branding

1. **Settings** → **Billing** → **Customer portal**
2. **Business information:**
   - **Headline:** `Beheer je Omni DJ-abonnement`
3. **Save**

#### Stap 5 — Stripe LIVE-mode (uit scope — pas ná Cloudflare/omni.com werkt)

`STRIPE-DNS-RUNBOOK.md` (post-rebrand: `STRIPE-DNS-RUNBOOK.md` met "Omni DJ" content) beschrijft de live-mode switch. **Niet in deze sessie.** Eerst TEST-mode stabiel onder nieuwe naam.

### 5.3 Cloudflare — omni.com vanaf scratch opzetten

Domein is bij een registrar gekocht (Sjuul moet bevestigen welke — zie OPEN VRAGEN). Cloudflare staat nog niet.

#### Stap 1 — Cloudflare-account + site toevoegen

1. Ga naar https://dash.cloudflare.com (login met je bestaande Sjuul-account dat al `clipdrop.com` heeft — zie HANDOVER-archive)
2. **+ Add a site** rechtsboven
3. Vul `omni.com` in → **Continue**
4. Kies plan: **Free** (voldoende voor landing + DNS + SSL)
5. Cloudflare scant DNS-records van de huidige registrar — meestal komen er een paar default-records terug. Verwijder die als ze niet gebruikt worden.
6. **Continue**

#### Stap 2 — Nameservers omzetten bij registrar

Cloudflare geeft je **2 nameservers** (vorm: `xxx.ns.cloudflare.com` + `yyy.ns.cloudflare.com`).

Log in bij de registrar waar `omni.com` is gekocht (Sjuul moet aanvullen — vermoedelijk TransIP, Namecheap of Cloudflare zelf).

- **Als Cloudflare Registrar:** geen verdere actie nodig, nameservers staan automatisch goed.
- **Als TransIP:** Mijn Domeinen → omni.com → Nameservers → "Eigen nameservers" → vul beide Cloudflare-nameservers in → Save.
- **Als Namecheap:** Domain List → Manage → Nameservers → "Custom DNS" → vul beide in → Save (groen vinkje).

DNS-propagatie duurt 1-24u. Cloudflare emailt zodra het actief is.

#### Stap 3 — DNS-records aanmaken voor omni.com

In Cloudflare dashboard → **DNS** tab:

| Type | Name | Content | Proxy status | TTL |
|---|---|---|---|---|
| A | `@` | (IP van landing-host, bv Vercel/Netlify) | Proxied (oranje wolkje) | Auto |
| CNAME | `www` | `omni.com` | Proxied | Auto |
| MX | `@` | `aspmx.l.google.com` (priority 1) | DNS only (grijs) | Auto |
| MX | `@` | `alt1.aspmx.l.google.com` (priority 5) | DNS only | Auto |
| MX | `@` | `alt2.aspmx.l.google.com` (priority 5) | DNS only | Auto |
| MX | `@` | `alt3.aspmx.l.google.com` (priority 10) | DNS only | Auto |
| MX | `@` | `alt4.aspmx.l.google.com` (priority 10) | DNS only | Auto |
| TXT | `@` | `v=spf1 include:_spf.google.com ~all` | DNS only | Auto |
| TXT | `@` | (DKIM-record uit Google Workspace — zie 5.4) | DNS only | Auto |
| TXT | `_dmarc` | `v=DMARC1; p=quarantine; rua=mailto:omnidj@monohq-labs.com` | DNS only | Auto |

**Let op:** als landing op Cloudflare Pages komt (zie 5.5), dan vervangen de eerste twee records door Pages' auto-aangemaakte CNAME.

#### Stap 4 — SSL/TLS modus

1. **SSL/TLS** tab → **Overview**
2. Set encryption mode to **Full (strict)** — vereist dat origin (Vercel/Netlify/Pages) ook HTTPS doet, wat ze allemaal automatisch doen.
3. **Edge Certificates** → toggle **Always Use HTTPS** AAN
4. **Edge Certificates** → toggle **Automatic HTTPS Rewrites** AAN

#### Stap 5 — Page Rules / Redirects (optioneel)

Niet nodig voor v1 — omni.com en www.omni.com gaan beide naar dezelfde landing.

### 5.4 Google Workspace — email-routing voor monohq-labs.com

Sjuul heeft de twee Gmail-accounts (`omnidj@monohq-labs.com` + `sjuul@monohq-labs.com`) al aangemaakt. Voor de tool moeten ze:

1. **App Password genereren voor Supabase SMTP** (al beschreven in 5.1 stap 4):
   - Voor `omnidj@monohq-labs.com`: log in → https://myaccount.google.com → **Security** → **2-Step Verification** moet AAN staan → **App passwords** → "Mail" + "Other (Custom name)" = "Supabase SMTP" → kopieer 16-char wachtwoord → plak in Supabase SMTP-settings.

2. **SPF/DKIM/DMARC** voor uitgaande mail vanaf `omnidj@monohq-labs.com`:
   - **`monohq-labs.com` is een ander domein dan omni.com.** Mail-routing moet daar geconfigureerd zijn (in Google Workspace admin van `monohq-labs.com`).
   - Aangezien Sjuul al de Gmail-mailboxes heeft, gaat Google Workspace daar al draaien. SPF (`v=spf1 include:_spf.google.com ~all`) en DKIM staan dan al goed.
   - **Verifieer** dat Workspace voor `monohq-labs.com` actief is — log in op https://admin.google.com en check **Apps → Google Workspace → Gmail**.
   - **DKIM:** Apps → Google Workspace → Gmail → **Authenticate email** → Generate new record → kopieer TXT-record → moet in DNS van `monohq-labs.com` (bij die registrar, niet bij omni.com).

3. **Email-aliassen toevoegen (optioneel maar handig):**
   - `support@omni.com` → forward naar `omnidj@monohq-labs.com`
   - `noreply@omni.com` → forward naar `omnidj@monohq-labs.com`
   - Configureer in Cloudflare Email Routing (gratis): Email tab → Routing → Create address → forward to `omnidj@monohq-labs.com`.

### 5.5 Cloudflare Pages — landing-deploy

De `landing/` folder is een statische site. Deploy via Cloudflare Pages voor gratis hosting + automatisch SSL + custom domain.

**Optie A — Via Git (aanbevolen):**

1. Maak nieuwe GitHub-repo aan: **`monolabs/omni-dj-landing`** (kies juiste owner — of `sjuulstudios/omni-dj-landing` als je geen MONO LABS GitHub-org hebt)
2. Push huidige `landing/` folder (na rebrand) naar die repo
3. Cloudflare Dashboard → **Workers & Pages** → **Create application** → **Pages** → **Connect to Git**
4. Authoriseer GitHub → selecteer `omni-dj-landing` repo
5. **Project name:** `omni-dj-landing`
6. **Production branch:** `main`
7. **Build settings:** geen build nodig (statische HTML), output directory `/`
8. **Save and Deploy** — krijg subdomain als `omni-dj-landing.pages.dev`
9. **Custom domains** → Set up custom domain → `omni.com` + `www.omni.com` → Cloudflare maakt automatisch de juiste DNS-records

**Optie B — Direct upload (sneller voor v1):**

1. Workers & Pages → Create → Pages → Upload assets
2. Upload `landing/` folder als zip
3. Project name + custom domain als Optie A

### 5.6 Apple Developer (codesigning)

**Geen actie nodig deze sessie** mits Sjuul z'n bestaande Apple Developer-account `business@sjuulstudios.com` blijft gebruiken.

**Maar:** de Bundle ID `com.sjuulstudios.cliplive` wordt vervangen door `com.monolabs.omnidj`. Apple wil je eventueel hebben dat je de nieuwe Bundle ID registreert bij https://developer.apple.com → Certificates, Identifiers & Profiles → Identifiers → +. Dit is ALLEEN strikt nodig als je de app submit aan de Mac App Store. Voor distributie via .dmg buiten de store is registratie van Bundle ID niet vereist — alleen valid Developer ID Application certificaat.

**Sub-task voor later:** Apple Developer-account transferren of nieuwe account aanvragen onder MONO LABS-naam ($99/jaar). Dat is OUT OF SCOPE voor de big-bang rebrand-sessie.

---

## 6. .app rebuild — nieuwe Bundle, schone install

Nadat code-side en folder-rename klaar zijn:

1. **Verifieer alle code-changes** (smoketests in dev-server vóór PyInstaller):
   ```bash
   cd ~/Documents/Claude/Projects/"Omni DJ"/"Omni DJ"
   ./start.sh
   ```
   Open `http://127.0.0.1:5555` — check: app-titel = "Omni DJ", footer = "by MONO LABS", login-flow werkt, localStorage-key `omniDj.session` wordt gezet bij login.

2. **Oude bundle weg uit `/Applications`:**
   ```bash
   rm -rf "/Applications/Clip Live.app"
   ```

3. **Oude user-data weg (geen users, dus geen verlies):**
   ```bash
   rm -rf "/Users/sjuulsmits/Library/Application Support/Clip Live"
   ```

4. **PyInstaller rebuild met nieuwe spec:**
   ```bash
   cd ~/Documents/Claude/Projects/"Omni DJ"/"Omni DJ"
   source venv/bin/activate
   ./build_macos.sh dmg
   ```
   Verwacht resultaat na 5-10 min: `dist/Omni DJ.app` + `dist/Omni DJ.dmg`.

5. **Sleep `Omni DJ.app` naar `/Applications`:**
   ```bash
   mv "dist/Omni DJ.app" "/Applications/"
   ```

6. **Open + test:**
   ```bash
   open "/Applications/Omni DJ.app"
   ```
   Verifieer: browser opent automatisch op `127.0.0.1:5555`, app-titel "Omni DJ", login werkt, nieuwe user-data folder `~/Library/Application Support/Omni DJ/` is aangemaakt.

7. **Codesign + Notarize** (alleen voor distributie aan derden — niet voor jezelf):
   ```bash
   export APPLE_DEVELOPER_ID="Developer ID Application: Sjuul Studios (TEAMID)"
   export APPLE_NOTARY_PROFILE=omnidj-notary
   ./build_macos.sh sign notarize dmg
   ```
   Voor de notary-profile moet je eerst (eenmalig):
   ```bash
   xcrun notarytool store-credentials omnidj-notary \
     --apple-id business@sjuulstudios.com \
     --team-id YOUR_TEAM_ID \
     --password YOUR_APP_SPECIFIC_PASSWORD
   ```

---

## 7. Code-side rebrand — exacte commando's (sed-based)

**Veiligheid:** alleen draaien NA volledige tar.gz-backup en NA git commit van huidige staat.

> **UPDATE 2026-05-28:** Werkdirectory is nu `~/Documents/Claude/Projects/Omni DJ/` (was `Clip Live` in oorspronkelijk plan). Subfolder heet `Omni DJ/` (was `dj-clip-cutter/`). Find-paths en launcher.py-pad zijn hieronder aangepast.

```bash
cd ~/Documents/Claude/Projects/"Omni DJ"

# 1. Git commit huidige staat als veiligheidsnet
git add -A && git commit -m "Pre-rebrand snapshot — alles vóór Omni DJ migratie"

# 2. Vind alle .py / .html / .css / .js / .md / .sh / .json / .ts / .sql / .spec / .plist files
# (sluit .bak / .backup / venv / __pycache__ / .git / dist / build / node_modules uit)
# Subfolder heet "Omni DJ" (sessie 59 rename) — vandaar de quoted glob.
FIND_CMD='find . -type f \( -name "*.py" -o -name "*.html" -o -name "*.css" -o -name "*.js" -o -name "*.md" -o -name "*.sh" -o -name "*.json" -o -name "*.ts" -o -name "*.sql" -o -name "*.spec" -o -name "*.plist" -o -name "*.toml" -o -name "*.xml" -o -name "*.svg" -o -name "*.txt" \) \
  -not -path "./.git/*" \
  -not -path "./venv/*" \
  -not -path "./Omni DJ/venv/*" \
  -not -path "*/__pycache__/*" \
  -not -path "./build/*" \
  -not -path "*/build/*" \
  -not -path "./dist/*" \
  -not -path "*/dist/*" \
  -not -path "./.backups/*" \
  -not -name "*.bak" \
  -not -name "*.backup*"'

# 3. SED-replace per variant — in volgorde van specifiek naar algemeen
# (BSD sed op Mac vereist '' na -i)

# 3a. Visible product-name varianten → "Omni DJ"
eval $FIND_CMD | xargs sed -i '' \
  -e 's/Clipdrop Live/Omni DJ/g' \
  -e 's/Clip Drop Live/Omni DJ/g' \
  -e 's/Clip Live/Omni DJ/g' \
  -e 's/Clipdrop/Omni DJ/g' \
  -e 's/Clip Drop/Omni DJ/g'

# 3b. URL/domain varianten
eval $FIND_CMD | xargs sed -i '' \
  -e 's|clipdroplive\.com|omni.com|g' \
  -e 's|djclips\.nl|omni.com|g' \
  -e 's|clipdrop\.com|omni.com|g'

# 3c. Bundle ID + env-vars + localStorage keys (LET OP: hoofdletter-gevoelig)
eval $FIND_CMD | xargs sed -i '' \
  -e 's/com\.sjuulstudios\.cliplive/com.monolabs.omnidj/g' \
  -e 's/CLIP_LIVE_USER_DATA/OMNI_DJ_USER_DATA/g' \
  -e 's/CLIP_LIVE_PORT/OMNI_DJ_PORT/g' \
  -e 's/CLIP_LIVE_BIND/OMNI_DJ_BIND/g' \
  -e 's/clipLiveRedesignV2/omniDjRedesignV2/g' \
  -e "s/'clipLive\\./'omniDj./g" \
  -e 's/"clipLive\./"omniDj./g' \
  -e 's/cliplive\.brandstack/omniDj.brandstack/g' \
  -e 's/clipLive\.session/omniDj.session/g' \
  -e 's/cliplive-track-/omnidj-track-/g' \
  -e 's/cliplive_dmg_settings/omnidj_dmg_settings/g' \
  -e 's/cliplive_restart/omnidj_restart/g' \
  -e 's/cliplive-launch/omni-dj-launch/g' \
  -e 's/cliplive-notary/omnidj-notary/g'

# 3d. ClipLive (PascalCase, alleen in spec/build)
eval $FIND_CMD | xargs sed -i '' \
  -e 's/ClipLive\.spec/OmniDJ.spec/g' \
  -e 's/ClipLive/OmniDJ/g'

# 3e. Sjuul Studios → MONO LABS in copyright-context
eval $FIND_CMD | xargs sed -i '' \
  -e 's/© 2026 Sjuul Studios/© 2026 MONO LABS/g' \
  -e 's/Sjuul Studios/MONO LABS/g'

# 3f. Wachtwoord-blacklist (auth.py:418)
eval $FIND_CMD | xargs sed -i '' \
  -e "s/'clipdrop1'/'omnidj1'/g" \
  -e "s/'clipdrop123'/'omnidj123'/g" \
  -e "s/'djclips01'/'omni1'/g" \
  -e "s/'djclips123'/'omni123'/g"

# 3g. Email-adressen
eval $FIND_CMD | xargs sed -i '' \
  -e 's/business@sjuulstudios\.com/omnidj@monohq-labs.com/g' \
  -e 's/business\+cliptest@sjuulstudios\.com/omnidj+test@monohq-labs.com/g'

# 4. macOS user-data folder-naam (in launcher.py)
#    LET OP: subfolder heet "Omni DJ" (post-sessie 59), niet "dj-clip-cutter".
sed -i '' \
  -e 's|"Application Support" / "Clip Live"|"Application Support" / "Omni DJ"|g' \
  -e 's|APPDATA.*"Clip Live"|APPDATA.*"Omni DJ"|g' \
  -e 's|".clip-live"|".omni-dj"|g' \
  "Omni DJ/launcher.py"

# 5. Hernoem spec-file
mv "Omni DJ/ClipLive.spec" "Omni DJ/OmniDJ.spec"

# 6. Verifieer dat er geen oude varianten resteren
eval $FIND_CMD | xargs grep -l -E "Clip Live|cliplive|ClipLive|Clipdrop|djclips|Sjuul Studios" || echo "✓ Alle varianten zijn weg"
```

**Na de sed-run:** handmatig nakijken:
- `landing/og-image.svg` — bevat brand-text als SVG paths/text, sed werkt meestal wel maar visueel checken
- Binary files (`.docx`, `.xlsx`) — apart openen en handmatig editen
- HANDOVER.md — review of context nog klopt (sommige session-summaries verwijzen naar specifieke "Clip Live"-momenten die historisch zijn)

---

## 8. Folder-renames (na sed-run)

> **UPDATE 2026-05-28 — STAP 8a, 8b en 8e ZIJN AL GEDAAN.** Sjuul deed de drie folder-renames handmatig in Finder tijdens sessie 59. Alleen de mockup-files (8c), business-model docs (8d) en git-commit (8f) staan nog open.

### 8.1 Reeds gedaan (sessie 59)

```bash
# 8a. Subfolder: dj-clip-cutter → Omni DJ (LET OP: twee keer Omni DJ in pad)
#     was: mv dj-clip-cutter omni-dj
#     werd: mv dj-clip-cutter "Omni DJ"   ← Sjuul koos title-case ipv kebab-case

# 8b. CLIP DROP DJ-SETS test-folder → OMNI DJ - TEST DJ-SETS

# 8e. Workspace-folder: Clip Live → Omni DJ
```

### 8.2 Nog uit te voeren in big-bang sessie

```bash
cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ"

# 8c. Mockup-bestanden in project-root
mv clip-live-redesign.html omni-dj-redesign.html
mv clip-live-redesign-v2.html omni-dj-redesign-v2.html
mv clip-drop-financial-dashboard.html omni-dj-financial-dashboard.html

# 8d. Business-model docs
mv business-model-2026/CLIP-LIVE-BUSINESS-MODEL-PLAN.docx business-model-2026/OMNI-DJ-BUSINESS-MODEL-PLAN.docx
mv business-model-2026/CLIP-LIVE-FINANCIEEL-MODEL.xlsx business-model-2026/OMNI-DJ-FINANCIEEL-MODEL.xlsx

# 8f. Git: commit alle rename-changes + sed-replace-changes uit sectie 7
git add -A
git commit -m "Rebrand: Clip Live → Omni DJ (sed-replace, Bundle ID, env-vars, mockup-renames)"
```

**Belangrijk over git:** `git mv` had handiger geweest voor renames, maar omdat de folder-rename buiten git zelf gebeurt (we hernoemen de root via Finder), zien latere `git status`-runs het als delete+add. Geen probleem voor de werking, alleen voor "view file history". Als blame/history op `app.py` later belangrijk is, gebruik dan `git log --follow app.py`.

---

## 9. GitHub repo's

Bestaande repo `sjuulstudios/djclips.nl-by-MONO-LABS` heet nog onder oude naam.

1. Ga naar https://github.com/sjuulstudios/djclips.nl-by-MONO-LABS
2. **Settings** → onder **Repository name**: rename naar **`omni-dj-landing`**
3. GitHub maakt automatisch redirect van oude naam → nieuwe naam
4. **Lokaal:** update remote-URL:
   ```bash
   cd ~/Documents/Claude/Projects/clipdrop-landing-deploy   # of waar de landing-deploy folder staat
   git remote set-url origin git@github.com:sjuulstudios/omni-dj-landing.git
   ```
5. **Optioneel:** transfer naar nieuwe GitHub-org `monolabs` als die bestaat. Settings → Transfer ownership → vul org-naam in. Vereist dat de target-org bestaat én dat jij admin rechten daar hebt.

Voor de **hoofdrepo** (`dj-clip-cutter`/`Omni DJ` source — als die in een git-remote staat):
- Check `git remote -v` in `~/Documents/Claude/Projects/Omni DJ/`
- Als er een remote is: rename die repo op GitHub + update local remote-URL

---

## 10. Verificatie-checklist (na alle stappen)

Loop dit af **na** de big-bang sessie om zeker te weten dat niks gemist is.

### Code/app

- [ ] `./start.sh` in `~/Documents/Claude/Projects/Omni DJ/Omni DJ/` start zonder errors
- [ ] Browser opent op `http://127.0.0.1:5555`, tab-title = "Omni DJ"
- [ ] Footer toont "Omni DJ by MONO LABS"
- [ ] Login-modal werkt; nieuwe localStorage-key `omniDj.session` wordt gezet
- [ ] Browser dev-tools → Application → Local Storage: alleen `omniDj.*` keys, geen `clipLive.*`
- [ ] Browser dev-tools → console: geen errors over "missing CLIP_LIVE_*" env-vars
- [ ] Dashboard rendert clips; existing user-data is verloren (verwacht — folder is gerenamed)
- [ ] Upload + drop-detectie werkt end-to-end
- [ ] Caption-export werkt (regressie-test sessie 50/52)
- [ ] `grep -r "Clip Live\|cliplive\|clipdrop\|djclips" --exclude-dir=.git --exclude-dir=venv --exclude="*.bak" .` returns leeg (of alleen historische log-strings die acceptabel zijn)

### Externe services

- [ ] Supabase project-naam = "Omni DJ" (zichtbaar links bovenin dashboard)
- [ ] Email-templates bevatten "Omni DJ" + "MONO LABS" footer + omni.com link
- [ ] Custom SMTP werkt (test: zelf password-reset aanvragen — mail komt van `omnidj@monohq-labs.com`)
- [ ] Beide admin-accounts hebben `role='admin'` + `plan='studio'` (SQL-query in 5.1 stap 5)
- [ ] Stripe products heten "Omni DJ — Pro" en "Omni DJ — Studio"
- [ ] Stripe public business name = "Omni DJ", statement descriptor = "OMNI DJ"
- [ ] Stripe Customer Portal toont "Omni DJ" branding
- [ ] Cloudflare: omni.com DNS-records actief, `ping omni.com` werkt (na propagatie 1-24u)
- [ ] omni.com laadt landing-pagina via HTTPS (groen slotje)
- [ ] DKIM/SPF/DMARC voor monohq-labs.com via Google Workspace verified (check via https://mxtoolbox.com)

### .app bundle

- [ ] Oude `/Applications/Clip Live.app` is weg
- [ ] `/Applications/Omni DJ.app` bestaat
- [ ] App opent zonder Gatekeeper-blokkade (gesigned + notarized)
- [ ] App-titel in menubar = "Omni DJ"
- [ ] `~/Library/Application Support/Omni DJ/` wordt aangemaakt bij eerste run
- [ ] `~/Library/Application Support/Clip Live/` is leeg/weggegooid

### Docs

- [ ] HANDOVER.md heet nog steeds HANDOVER.md (filename) maar interne inhoud zegt "Omni DJ"
- [ ] CLAUDE.md gebruikt nieuwe paden + naam
- [ ] QUICK-REFERENCE.md heeft juiste `cd`-commando met "Omni DJ"-pad
- [ ] Alle SESSIE*.md files zijn aangepast aan nieuwe naam (zie sectie 3.5)

---

## 11. Memory-updates voor toekomstige sessies

Na de uitvoering moet je **deze memory-files updaten** zodat volgende Cowork-sessies de nieuwe context kennen:

- `project_startup_path.md` → nieuwe pad + commando
- `project_clip_live.md` → renamen naar `project_omni_dj.md`, brand-direction updaten
- `reference_clip_live_files.md` → renamen naar `reference_omni_dj_files.md`, alle paden aanpassen
- `project_clip_drop_stripe_overview.md` → renamen, Stripe-context updaten
- `project_clip_live_paid_architecture.md` → renamen
- `project_clip_live_security.md` → renamen
- Alle `project_sessie*` memory-files → mentions van "Clip Live" / paden updaten

Nieuwe memory:
- `project_omni_dj_rebrand_2026_05_27.md` — dat de rebrand is uitgevoerd, op welke datum, welke services geraakt
- `reference_admin_emails.md` — `omnidj@monohq-labs.com` (system) + `sjuul@monohq-labs.com` (Sjuul), beide `role='admin'` + `plan='studio'` in Supabase

Memory-index `MEMORY.md` updaten met de renames.

---

## 12. Risico's + rollback

### Risico's

| Risico | Impact | Mitigatie |
|---|---|---|
| Sed-regex matched per ongeluk iets verkeerd (bv. "Clip Live" in een externe library-name) | Mid — build-error of runtime-crash | Pre-rebrand git commit (sectie 7 stap 1) → `git diff` review per file vóór commit |
| Folder-rename verbreekt PyInstaller-bundle die nog in dist/ staat | Laag — dist/ wordt opnieuw gegenereerd | Eerst `rm -rf dist/ build/` vóór rebuild |
| Supabase email-templates verwijzen naar oude URL nadat we ze hebben overgeschreven | Laag — Sjuul checkt visueel | Stap 5.1 stap 2 inclusief visuele verificatie |
| Cloudflare nameserver-switch duurt 24u → omni.com niet meteen bereikbaar | Laag — TEST-mode Stripe werkt nog op Supabase-URL | Plan stap 5.5 (Pages-deploy) pas uitvoeren ná DNS-propagatie |
| Apple-cert blijft op naam "Sjuul Studios" terwijl bundle-name "Omni DJ" is | Laag — codesign werkt mits cert geldig is; alleen rare cosmetische mismatch | Sub-task voor later: nieuwe cert onder MONO LABS aanvragen |
| `.env` met secrets staat in git (oud probleem) | HOOG — was al een issue vóór rebrand | OUT OF SCOPE deze sessie. Wel noteren als security-task. |
| Sjuul vergeet Claude desktop-app folder-pointer te updaten | Laag — Sjuul ziet errors over folder-not-found | Stap 4.6 in folder-rename runbook expliciet vermeld |

### Rollback

Als de big-bang halverwege misgaat:

1. **Tijdens code-rebrand (folder-rename is al gedaan in sessie 59):**
   ```bash
   cd ~/Documents/Claude/Projects/"Omni DJ"
   git reset --hard HEAD   # rollback naar pre-rebrand commit
   ```
   Folders blijven `Omni DJ/Omni DJ/` (al hernoemd). Alleen code-changes terug naar pre-rebrand staat.

2. **Volledige rollback uit tar.gz (van sectie 4.1):**
   ```bash
   cd ~/Documents/Claude/Projects
   rm -rf "Omni DJ"   # let op: alles weg
   tar -xzf omni-dj-pre-rebrand-YYYYMMDD.tar.gz
   ```
   Resultaat: `Omni DJ/Omni DJ/`-folder-structuur terug naar staat vóór de big-bang sessie (= sessie 59 staat = folders al hernoemd, code nog "Clip Live").

3. **Externe services rollback:**
   - Supabase project-naam: ga terug naar dashboard, rename "Omni DJ" → "Clip Drop Live"
   - Stripe products: rename terug
   - Cloudflare: laat staan (geen kwaad — domein is sowieso nieuw)

---

## 13. Volgorde-overzicht — wat-na-wat in de big-bang sessie

> ✅ **Reeds gedaan** (sessie 59, 28 mei): folder-renames + live code-paden gepatcht (zie HANDOVER + sectie 4-update). Wat hieronder volgt is wat nog open staat.

1. **Pre-flight checks** (sectie 4.1): tar-backup van `Omni DJ/`, dev-server stoppen, `Clip Live.app` uit `/Applications`, oude `~/Library/Application Support/Clip Live/` weggooien
2. **Code-side sed-run** (sectie 7): in volgorde 3a → 3g + launcher.py-pad + mv spec-file naar `OmniDJ.spec`
3. **Resterende folder/file-renames** (sectie 8.2): mockup-HTMLs in project-root + business-model docx/xlsx
4. **Git commit** rebrand-staat
5. **Smoketests in dev-server** (sectie 10 code/app block): start.sh vanuit `Omni DJ/Omni DJ/`, login, upload, export
6. **Supabase aanpassingen** (sectie 5.1): rename project + email-templates + SMTP + URL-allowlist
7. **Sign up admin-accounts** + SQL-update voor whitelisting (5.1 stap 5)
8. **Stripe aanpassingen** (sectie 5.2): account-branding + products renamen
9. **Cloudflare setup** (sectie 5.3 + 5.4 + 5.5): nameservers + DNS-records + Pages-deploy
10. **PyInstaller rebuild** (sectie 6): clean build, .dmg, install nieuwe `Omni DJ.app`
11. **End-to-end test** met `Omni DJ.app` uit `/Applications`
12. **Memory-files updaten** (sectie 11)
13. **HANDOVER.md afsluiten** met sessie-summary van rebrand

Verwachte totale tijd: **3-5 uur actieve tijd** + 1-24u DNS-propagatie passief (was 4-6u — folder-renames eraf).

---

## 14. OPEN VRAGEN (vóór uitvoering te beantwoorden)

Deze punten kwamen naar boven tijdens de scan en moet je beslissen vóór de big-bang sessie kan beginnen:

1. **Bij welke registrar staat omni.com geregistreerd?** (TransIP / Namecheap / Cloudflare Registrar / anders) — bepaalt sectie 5.3 stap 2.
2. **Bestaat GitHub-org `monolabs`?** Zo niet: gebruik je `sjuulstudios/omni-dj-landing` of maak je eerst de org? — bepaalt sectie 9.
3. **Apple Developer-account:** blijf je `business@sjuulstudios.com` gebruiken (en daarmee `Developer ID Application: Sjuul Studios (TEAMID)` als signing identity)? Of wil je dat al meteen naar MONO LABS migreren ($99/jaar nieuwe sub)? Sub-task of in scope?
4. **Stripe entity:** je Stripe-account staat op naam van "Sjuul Studios" (KvK). Voor verkoop onder "MONO LABS" moet de business-info in Stripe daadwerkelijk MONO LABS noemen — wat juridisch betekent: óf KvK-naam wijzigen van je eenmanszaak, óf nieuwe MONO LABS-entity oprichten + nieuwe Stripe-account. **In de tussentijd:** ik raad aan public-facing "Omni DJ by MONO LABS" maar Stripe-receipts blijven op huidige entity tot juridische rebrand. → Vraag aan jou: hoe wil je dit framen?
5. **`.env` met secrets in git-repo:** is een bestaand probleem (zie audit 2026-05-12). Wil je tijdens de rebrand-sessie ook `.env` uit history scrubben + secrets roteren? Of OUT OF SCOPE?
6. **Workspace-folder hernoemen via macOS vs git:** Mac Finder rename + `git mv` werken niet samen — wat is je voorkeur?
7. **Oude `~/Documents/Claude/Projects/clipdrop-landing-deploy/`-folder** (separate landing-deploy git-clone uit HANDOVER-archive) — bestaat die nog? Zo ja: ook rebranden of weggooien?
8. **Visual identity:** je zei "ben ik nog mee bezig". Wil je een placeholder MONO LABS-logo en Omni DJ-text-mark voor in de UI, of laten we de huidige look (warm cream + amber) staan en doen we visual-refresh als aparte sessie ná de naam-rebrand?

---

## 15. Wat dit plan **niet** doet

Expliciet uit scope (per jouw beslissing of vanwege risico):

- ❌ Stripe LIVE-mode activeren — eerst stabiel onder Omni DJ in TEST-mode
- ❌ Marketing-launch / beta-uitnodiging-mails — [[feedback_beta_flyer_skip]]
- ❌ Nieuw logo / visual identity-refresh — Sjuul werkt hier nog aan
- ❌ Apple Developer-account migratie naar MONO LABS — sub-task
- ❌ Stripe entity wijzigen (Sjuul Studios → MONO LABS KvK) — juridische sub-task
- ❌ `.env`-secrets roteren (Supabase, Stripe) — sub-task of behouden tenzij Sjuul kiest
- ❌ Git-history rewriten — commits behouden hun oude messages
- ❌ Backup-bestanden (`.bak`) rebranden — historische snapshots, weggooien optioneel
- ❌ Multi-tenant / multi-artist features uit `PLAN-CONTENT-CALENDAR-2026-05-26.md`
- ❌ Tweede tool onder MONO LABS-suite (alleen Omni DJ in deze sessie)

---

**Einde plan.** Vragen 1-8 in sectie 14 beantwoorden vóór uitvoering. Dan ben je klaar om de big-bang sessie in te plannen — alles wat je hierboven leest is dan letterlijk uit te voeren.
