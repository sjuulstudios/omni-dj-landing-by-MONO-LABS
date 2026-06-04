# PLAN - Echte 1:1 + 4:5 crops + per-ratio naamgeving + Downloads-default

Sessie 75 (2026-06-04). Gericht plan voor 1 samenhangende feature in de export-flow.
Bouwen pas na akkoord. Alles op de dev-server (:5599) bouwen en testen; gaat mee in de
volgende batch-rebuild (samen met de al gemaakte logo-fix + picker-fix).

## Doel (wens Sjuul)
1. De formaten 1:1 en 4:5 moeten ECHTE crops worden (nu mappen ze in `startExport` allebei
   op de vertical-bron -> je krijgt een kopie van 9:16, geen echte vierkante/4:5 video).
2. Elke gekozen ratio levert 1 bestand, met naam = rename-basis + " - <ratio>".
   Voorbeeld rename "House set": "House set - 9x16.mp4", "House set - 16x9.mp4",
   "House set - 1x1.mp4", "House set - 4x5.mp4".
3. Export-map: default = de Downloads-map, vooraf geselecteerd. Geen map gekozen ->
   duidelijke melding dat de gebruiker eerst een map moet kiezen voordat de export start.

## Huidige staat (geverifieerd in de code)
- Cutter maakt nu 2 echte crops: 9:16 (`_get_vertical_crop` + `_build_vertical_cmd`, center-crop
  -> 1080x1920) en 16:9 (`_build_landscape_cmd` -> 1920x1080). Geen 1:1 of 4:5.
- `startExport` (static/index.html ~r.18093) mapt 9:16->vertical, 16:9->landscape, en 1:1 + 4:5
  -> vertical (collapse). Backend `_run_export_job` (app.py r.6888) filtert aspects tot alleen
  landscape/vertical. Dus 1:1 en 4:5 bestaan nu niet echt.
- Bestandsnaam: `_build_export_filename` (app.py r.6570) = `<label>` voor 9:16 en `<label>_landscape`
  voor 16:9. Library leest aspect uit de sidecar `.meta.json`, dus naamgeving wijzigen breekt de
  Library niet.
- Export-map: modal default = "Default (Library)" (= OUTPUT_DIR). `KIES MAP` -> `/api/pick-folder`.
  Geen Downloads-default.

## Aanpak

### A. Echte crops in de cutter (kern, hoogste risico)
- Nieuwe center-crop-berekening voor 1:1 en 4:5, analoog aan `_get_vertical_crop`
  (target_ratio 1/1 en 4/5), met scale naar 1080x1080 (1:1) en 1080x1350 (4:5).
- Crop-framing: CENTER (zelfde keuze als de huidige vertical center-crop). Eenvoudig,
  voorspelbaar; fijn-tunen (drop-centrering/tracking) kan later. <- open beslissing, zie onder.
- Brand-overlays (logo/watermark/captions) meenemen via dezelfde `_maybe_compose_brand_vf`
  zodat de nieuwe formaten net als 9:16/16:9 de brand bakken.
- Genereren ON-DEMAND bij export (in de prebake/recut-route), NIET bij elke analyse
  (anders bloat: 4 formaten x elke clip). Analyse blijft 9:16 + 16:9 voor de preview.
- Touch-points te verifieren tijdens bouw: `recut_clip` (formats-lijst uitbreiden naar
  square/portrait45), `_resolve_export_sources` + `_prebake_clip_for_export` (app.py),
  en de aspect->bestandsnaam-suffix in de cutter-output.

### B. Frontend mapping + backend filter
- `startExport`: 1:1 -> `square`, 4:5 -> `portrait45` (stop de collapse naar vertical).
- `_run_export_job` aspect_filter (app.py r.6888): `square` en `portrait45` toelaten.
- Sidecar-aspectmap in `/api/exports` (app.py r.7430): `portrait45` toevoegen (nu staat er
  alleen `portrait`) zodat de Library 4:5 juist labelt.

### C. Per-ratio naamgeving
- `_build_export_filename`: aspect -> ratio-token map { vertical:9x16, landscape:16x9,
  square:1x1, portrait45:4x5 }, en bestandsnaam = `<label> - <ratio>` (join met " - ").
- Label-basis: spaties behouden (alleen echt illegale tekens strippen: \ / : * ? " < > |),
  zodat "House set" "House set" blijft. Dubbele punt vermeden -> "9x16" i.p.v. "9:16"
  (veilig op macOS en Windows). Codec-suffix (bij non-match) blijft als " - h265" e.d.
- Sidecar blijft geschreven -> Library blijft werken.

### D. Downloads-default + verplichte map
- Nieuw `GET /api/default-export-dir` -> { path: ~/Downloads (expanduser), label: "Downloads",
  exists: bool }. (Binnen home, dus voldoet aan de bestaande home-whitelist.)
- Modal: bij openen default `currentOutputDir` = Downloads-pad, toon "Downloads" als
  geselecteerd (i.p.v. "Default (Library)"). Onthoud laatst gekozen map zoals nu.
- Bij Export: als er geen geldige map is -> blokkeer + duidelijke toast "Kies eerst een
  download-map" (geen stille fallback naar Library).
- Backend `api_export_start`: als geen output_dir meegegeven -> default ~/Downloads (vangnet).

## Bouwvolgorde (per stap testen op :5599)
1. C (naamgeving) + D (Downloads) eerst: laag risico, direct zichtbaar, raakt de cutter niet.
2. A (echte crops) daarna: de risicovolle kern, met backup van cutter.py vooraf en
   frame-checks (1:1 -> 1080x1080, 4:5 -> 1080x1350, brand bakt) per formaat.
3. B (mapping/filter) sluit A aan op de UI.
4. E2E: alle vier de formaten exporteren uit 1 set, frame-check afmetingen + brand + namen,
   Library toont ze met juiste ratio, Downloads-default werkt.

## Risico's / let op
- Cutter is de kern van de werkende export-pijplijn. Backup `cutter.py.pre-sessie75-ratios.bak`
  + `app.py`-backup vooraf. Niet de bestaande 9:16/16:9-paden herschrijven, alleen uitbreiden.
- Stream-copy ("Match source") kan geen crop -> voor 1:1/4:5 is altijd een re-encode nodig
  (zoals vertical/landscape met overlays ook al re-encoden). Checken dat codec=match hier
  netjes naar een re-encode valt voor de nieuwe formaten.
- Tracking (pan/zoom keyframes) bestaat alleen voor vertical; 1:1/4:5 krijgen v1 een vaste
  center-crop (geen tracking). Prima voor v1.

## Open beslissing voor jou
- Crop-framing 1:1 en 4:5: CENTER-crop (mijn voorstel, simpel) of wil je dat ze de drop
  net als 9:16 centreren/volgen (meer werk)? Voor v1 raad ik center aan.
- Ratio-token in de bestandsnaam: "9x16" (mijn voorstel, veilig) of liever "9-16"?
