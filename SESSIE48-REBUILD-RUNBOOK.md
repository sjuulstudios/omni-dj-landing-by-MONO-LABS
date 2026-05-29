# SESSIE 48 — Rebuild & smoketest runbook (unsigned testbuild)

> **Voor Sjuul.** Eén commando per regel. Geen markdown fences in commando's.
> Alle paden tussen quotes (er staan spaties in). Stop bij elke vraag of
> error en meld wat je ziet — ga niet door naar de volgende stap voor je
> bevestiging hebt.

Deze rebuild is nodig omdat de huidige `.app`/`.dmg` in `dist/` van vandaag
08:28 is — vóór sessies 41 t/m 48. Inmiddels zit er 7 sessies aan
wijzigingen tussen die build en de huidige code-state.

Wat zit er nieuw in deze build (sinds laatste .dmg van 08:28):

- Sessie 41+42 — fonts-systeem (ClipLivePicker, 11 built-in fonts,
  system-font scan ~438 op Mac, refresh-knop), 3 font-bronnen merged in cutter
- Sessie 43a+43b — export-pipeline fix: auto-bake captions in export, rename-veld
  in modal, schone filenames + sidecar, ratio-tiles, caption/wm toggles,
  folder-whitelist user-home only, queue-bar
- Sessie 44 — selectie-preview-balk onderaan editor
- Sessie 45 — v2 shell achter feature-flag `localStorage.clipLiveRedesignV2='1'`
- Sessie 46 — v2 dashboard / clips-grid (CSS-only)
- Sessie 47 — v2 editor / timeline / drawers (CSS-only)
- Sessie 48 — v2 modals (auth/wizard/forgot/upgrade/aspect/export-settings, CSS-only)

Deze runbook is voor een **unsigned testbuild** (jouw keuze in sessie 48).
Dat is `./build_macos.sh dmg` zonder sign/notarize. Werkt op jouw eigen Mac,
nog niet geschikt voor distributie naar klanten. Sign+notarize komt later
wanneer alle features groen getest zijn.

---

## Stap 0 — Pre-build dev-server smoketest

Eerst nog één keer testen dat alles draait op de dev-server, vóór we
gaan bundelen. Als hier iets faalt, geen zin om een .app te bouwen.

Server starten (sluit eerst andere dev-servers af met Ctrl+C):

cd "/Users/sjuulsmits/Documents/Claude/Projects/Clip Live/dj-clip-cutter"

./start.sh

Open in browser: http://127.0.0.1:5555

### 0.1 — Smoketest met feature-flag UIT (oude UI)

Eerst zonder de v2-redesign, om te bevestigen dat de oude flow nog 100% werkt.

In DevTools console (F12):

localStorage.setItem('clipLiveRedesignV2','0')

Reload de pagina.

Check:

1. Login werkt nog (jouw bestaande account)
2. Upload-pagina is de oude UI (sidebar links: Clip Live / Drop a set / Library / Clips / Brand Stack / Settings)
3. Open een bestaande set → clip-grid laadt in oude stijl
4. Open een clip in de editor → trim/text/track-drawers werken
5. Export single clip → aspect-modal opent in **oude stijl** (controle: scrim is warm-dark, niet pure zwart)
6. Klik "Forgot password?" op login-scherm → forgot-modal opent in **oude stijl** (warm-amber button)

Als één van deze 6 punten faalt, stop en meld het.

### 0.2 — Smoketest met feature-flag AAN (v2-redesign)

In DevTools console:

localStorage.setItem('clipLiveRedesignV2','1')

Reload de pagina.

Check (Fase 1 — shell):

1. V2-sidebar verschijnt: workspace-button bovenaan ("Sjuul Studios · Pro plan") + 5 nav-items (Clips / Brand / Social / Calendar / Insights) + Settings-footer onderin
2. Topbar met breadcrumb "Clips"
3. Linksonder zit een klein `v2 shell`-toggle-knopje (label "ON")

Check (Fase 2 — dashboard):

4. Pick-head boven de clip-grid: titel + meta (BPM + duur)
5. Filter-chips zijn radius-16 pills (All / Drops / Favourites / Renamed)
6. Ratio-toggle is segmented control (9:16 / 16:9)
7. Hover op een clip-card → rond select-toggle-cirkeltje verschijnt links-boven
8. Klik dat cirkeltje → card krijgt oranje border + selectie-balk verschijnt bovenaan ("1 selected" + Cancel + oranje Export 1)
9. **Sessie 44 selectie-preview-balk** verschijnt onderaan met tile-thumb + label + Clear-knop

Check (Fase 3 — editor):

10. Klik op een clip-card body → editor opent in v2-stijl
11. Crumbs bovenaan ("Clips › [setnaam] › Clip XX · drop @ ...") + v2 back-button
12. Cue-points-panel links: titel + meta + filter-chips als pills + cue-rows als kaartjes
13. Ratio-rail segmented control (9:16 / 1:1 / 16:9 / 4:5)
14. Tool-rail rechts: Trim / Text / Track + Export-pill onderaan
15. Klik op Text → drawer opent rechts in v2-stijl, "+ Add text" knop met dashed border
16. Timeline onderaan: tl-toolbar met play-button in accent, snap/loop toggles, trim-handles in accent

Check (Fase 4 — modals):

17. Export single clip → aspect-modal opent met **scrim rgba(8,8,10,0.78)** + backdrop-blur + auth-card in dark-mode-stijl
18. Klik "Forgot password?" (eerst uitloggen via Settings) → forgot-modal in v2-stijl: compacte 420px kaart, submit-knop in oranje accent, geen oude warm-amber
19. Probeer een functie te gebruiken die over je quota gaat (of forceer via /api) → upgrade-modal opent met subtiele accent-gradient bovenaan + price-tag in oranje accent

Check (Sessie 41+42 — fonts):

20. Editor → Text-drawer → "+ Add text" → FONT-veld → klik de font-picker → er verschijnt een dropdown met de 11 built-in fonts bovenaan + system-fonts daaronder (op Mac ~438)
21. Refresh-knop naast font-picker werkt (system-font scan opnieuw)

Check (Sessie 43a+43b — export):

22. Selecteer 1 clip → klik Export → aspect-modal → kies 9:16 → klik Export
23. Op de quota-bar zie je een queue-bar verschijnen (één job in flight)
24. Open de output-folder → het MP4-bestand heeft een **schone filename** (geen UUID, geen onderscore-soep) + naast het MP4 ligt een sidecar JSON met metadata
25. Open het MP4 → **captions zijn ge-baked in** (sessie 43 blocker-fix)
26. Probeer een rename via het inline-editor-veld → MP4 wordt hernoemd op disk
27. Folder-whitelist: probeer een output-folder buiten je home-dir → blokkade-melding

Als één van deze 27 punten faalt, **stop, sluit de dev-server, en meld
welk punt + welke exacte error in de browser-console (F12) of in de
terminal staat**. Niet doorgaan naar Stap 1.

---

## Stap 1 — Geen edge-function deploy nodig

Sinds sessie 31 zijn de Supabase Edge Functions (`update-usage`,
`create-checkout-session`, `create-portal-session`, `stripe-webhook`)
niet meer aangepast. Skip deze stap.

Als je twijfelt: in het Supabase dashboard
https://supabase.com/dashboard/project/lbabsffxefkrxwzkbzar/functions
moeten alle 4 functions "Active" staan met groen vinkje.

---

## Stap 2 — Build de unsigned .dmg

Dev-server afsluiten met Ctrl+C in de terminal waar `./start.sh` draait.
Dan:

cd "/Users/sjuulsmits/Documents/Claude/Projects/Clip Live/dj-clip-cutter"

source venv/bin/activate

Je prompt moet nu (venv) ervoor hebben staan. Zo niet, stop en meld.

Controleer dat PyInstaller en dmgbuild geïnstalleerd zijn:

pip show pyinstaller dmgbuild

Als één van beide "WARNING: Package(s) not found" geeft, eerst installeren:

pip install pyinstaller dmgbuild

Dan de build:

./build_macos.sh dmg

Wat dit doet: bouwt `dist/Clip Live.app` en `dist/Clip Live.dmg`. Duurt
~5 minuten. Veel output is normaal. De defensieve secrets-scan uit
sessie 30 controleert of er per ongeluk .env of service_role keys in
de bundle zitten — die check moet groen blijven.

**Verwacht eind-resultaat:**

dist/Clip Live.app
dist/Clip Live.dmg  (~170-180 MB)

Als de build faalt:

- Lees de laatste 20 regels output
- Meld de exacte error
- **Niet** zelf gaan dingen aanpassen aan ClipLive.spec of build_macos.sh

---

## Stap 3 — Bundle-smoketest op de gebundelde .app

Eerst de oude `.app` uit `/Applications` weghalen (als die er staat):

rm -rf "/Applications/Clip Live.app"

Open de nieuwe `.dmg` en sleep `Clip Live.app` naar `/Applications`:

open "dist/Clip Live.dmg"

Sleep de app handmatig in het Finder-venster naar de Applications-pijl.
Sluit het .dmg venster.

Strip Gatekeeper-quarantine zodat hij meteen opent (alleen nodig op
**jouw** Mac omdat de build unsigned is):

xattr -dr com.apple.quarantine "/Applications/Clip Live.app"

Open vanuit Applications via rechts-klik → Open → bevestig.

Browser opent automatisch op http://127.0.0.1:5555 (of een ander
poortnummer als 5555 bezet is — dan staat het in `launcher.log`).

### 3.1 — Bundle-smoketest checks

Doe deze in deze volgorde, één voor één:

1. App opent → login-scherm in **v2-stijl** verschijnt (sessie 48 effect: dit is de eerste indruk voor nieuwe users)
2. Log in met je bestaande account
3. Quota toont correcte waarde uit Supabase (bv. 6/10 sets)
4. Sidebar v2 is actief (feature-flag staat default uit; hij staat hier mogelijk default uit — als hij UIT staat, schakel hem in via DevTools en reload, dan zie je v2)
5. Upload een korte test-mp4 (mag 30 sec zijn) → drop-detectie draait
6. Quota gaat van 6/10 naar 7/10 (of jouw plan-limiet)
7. Open een clip in de editor → **GEEN BPM-stamp** rechtsboven preview
8. Track-drawer toont drie opties incl. "Fit (no zoom)"
9. Brand Stack secties zijn inklapbaar
10. Watermark upload werkt
11. **Sessie 41+42** — Editor → Text → font-picker → 11 built-in + system-fonts laden
12. **Sessie 43** — Export single clip → MP4 bevat captions baked-in
13. **Sessie 43** — Filename is schoon (geen UUID-prefix)
14. **Sessie 43** — Sidecar JSON ligt naast het MP4
15. **Sessie 44** — Selecteer 2 clips → selectie-preview-balk verschijnt onderaan editor
16. Stripe checkout — klik "Upgrade to Pro" → opent checkout.stripe.com (TEST-mode kaart 4242 4242 4242 4242 / willekeurige CVC / toekomstige expiry)

Als één van deze 16 punten faalt:

- Open `launcher.log` (staat in `~/Library/Application Support/Clip Live/`)
- Meld het exacte punt + de laatste 20 regels uit `launcher.log`

---

## Stap 4 — Rapporteer terug

Stuur me:

- ✅ Welke stappen werkten (0.1, 0.2, 2, 3.1)?
- ❌ Welke faalden, met exacte error?
- Bytes-grootte van de gegenereerde `.dmg`
- Screenshot van de v2-stijl login (sessie 48 modals)
- Screenshot van een geëxporteerde clip met baked-in caption (sessie 43)

---

## Als iets stuk is — rollback-opties

Alle backups staan in `dj-clip-cutter/`. Eén voor één, niet allemaal tegelijk.

**Fase 4 modals stuk? (sessie 48)**

cp "static/index.html.pre-redesign-fase4.bak" "static/index.html"

./start.sh

**Fase 3 editor stuk? (sessie 47)**

cp "static/index.html.pre-redesign-fase3.bak" "static/index.html"

./start.sh

**Fase 2 dashboard stuk? (sessie 46)**

cp "static/index.html.pre-redesign-fase2.bak" "static/index.html"

./start.sh

**Hele v2 stuk? Terug naar pre-redesign (sessie 44):**

cp "static/index.html.pre-redesign-v2.bak" "static/index.html"

./start.sh

**Backend stuk (sessie 43 export)?**

cp "app.py.pre-sessie43-autobake.bak" "app.py"

cp "cutter.py.pre-sessie42.bak" "cutter.py"

./start.sh

---

## Wat is uit scope deze build

- Apple Developer signing → komt in latere sessie als deze build groen is
- Notarization → idem
- Windows .exe → fase 5 in INSTALLER-RUNBOOK.md, later
- Stripe LIVE-mode → blijft op TEST tot volledige distributie-build
- Fase 5 echte Social/Calendar/Insights features → komt na rebuild als jij dat wilt

---

## Bekende valkuilen

- **Bundle is ~400-700 MB** door librosa+scipy+numba. Niet in te krimpen
  zonder drop-detectie te slopen.
- **Eerste opening duurt 10-30 sec** terwijl numba modules JIT-compileert.
  Normaal, gebeurt alleen de eerste keer.
- **Feature-flag default** — als de v2-flag default UIT staat in de bundle,
  zie je oude UI bij eerste opening. Dat is correct (non-destructief uitrol).
  Om v2 te zien: F12 → console → `localStorage.setItem('clipLiveRedesignV2','1')` → reload.
- **AntiVirus / Gatekeeper** kan unsigned bundles flaggen. Voor jouw Mac:
  `xattr -dr com.apple.quarantine ...` oplost. Voor klanten: signing nodig.
