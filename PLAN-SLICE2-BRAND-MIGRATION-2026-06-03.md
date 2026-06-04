# PLAN Slice 2 - Brand bron-migratie (volledig, gefaseerd)

Datum: 2026-06-03 (sessie 74). Keuze Sjuul: volledige bron-migratie (niet alleen additief).
Regel: geen em-dashes/en-dashes. Per fase bouwen, testen, dan pas verder. Backup voor elke risky change.

---

## Doel

Vandaag is `brand_kit.json` een GLOBAAL bestand (1 per machine) achter `/api/brand-kit*`, gebruikt door de
Brand Stack-view en door de export/render. Het is niet per artist. Doel: het brand-profiel wordt per workspace
(artist), met Supabase (`dj_profiles`) als bron van waarheid en een lokale per-workspace cache voor snelheid en
voor de render-pijplijn. Artist A mag het profiel van B nooit zien.

Belangrijk: de render/export-pijplijn leest nu `STATE.brandKit` (frontend) en het lokale `brand_kit.json`
(backend). Die moeten per workspace gaan, zonder de werkende export te breken. Daarom gefaseerd, met een harde
checkpoint vlak voor de fase die de export raakt.

---

## Canoniek profiel-schema (`dj_profiles.profile` jsonb)

Superset zodat er niets verloren gaat. De rijke moat-velden plus het bestaande brand-kit ingebed onder een
sleutel, zodat de render-laag dezelfde vorm kan blijven lezen vanuit de cache:

```
profile = {
  schema_version: 1,
  artist_name, alias,
  visual:       { logo, logo_position, logo_size, primary_color, secondary_color, accent_color },
  typography:   { title_font, caption_font, caption_style },
  lower_third:  { enabled, template, duration },
  cta:          { style, spotify_link, beatport_link, show_in_last_seconds },
  hashtags:     { tiktok[], instagram[], youtube_shorts[] },
  caption_voice:{ tone, use_emojis, max_length_chars },
  brand_kit:    { ...het bestaande brand_kit.json blok: fonts, palette, logo, watermark,
                   caption_presets, handle, tagline, bpm_stamp, end_card... }
}
```

De `brand_kit`-sleutel houdt de huidige render-shape intact (verliesvrije migratie). De nieuwe velden
(cta/hashtags/caption_voice/alias/lower_third) leven ernaast en worden in fase 3/Slice 3 echt toegepast.

---

## Fasen

### Fase 1 - Niet-destructief backend-fundament (NU, additief)
Wat: nieuwe routes `GET/PUT /api/brand/profile`, workspace-scoped via `_user_supabase` + `current_workspace_id`.
Lezen: bestaat er nog geen `dj_profiles`-rij voor deze workspace, dan eenmalig SEEDEN uit het huidige globale
`brand_kit.json` (canoniek object bouwen) en upserten. Schrijven: valideren/mergen en upserten via de user-JWT
(RLS is de grens). `brand_kit.json` en alle `/api/brand-kit*` blijven exact zoals ze zijn; niets wordt omgelegd.
Raakt: alleen nieuwe code in `app.py`. Render/export ongemoeid.
Risico: laag (additief, omkeerbaar).
Test: ingelogd op :5599 (na restart): `GET /api/brand/profile` geeft het geseedede profiel voor workspace "TEST";
`PUT` slaat op; cross-account: een 2e account ziet het profiel van "TEST" niet (RLS).
Checkpoint: geen (additief). Na groen: door naar fase 2 NA jouw akkoord.

### Fase 2 - VERFIJND na diagnose (cutter leest globaal brand_kit.json zelf)

Diagnose-vondst: de cutter (`cutter.py` `_load_brand_assets_for_job`, regel 877) leest het GLOBALE
`brand_kit.json` rechtstreeks van schijf (`os.path.join(here, 'brand_kit.json')`), los van app.py. Jobs zijn
getagd met `user_id` maar NIET met een workspace, en logo/watermark gebruiken vaste bestandsnamen in gedeelde
mappen. Daarom is Fase 2 gesplitst:

#### Fase 2a - brand-metadata per workspace via mirror (GEBOUWD + GROEN, geen export-impact)
Wat: het globale `brand_kit.json` blijft exact zoals het is (cutter-bron, nul regressie). Elke brand-kit-save
(`_save_brand_kit`) schrijft het globale bestand EN mirrort de metadata naar `dj_profiles.profile.brand_kit` van
de actieve workspace (via `_user_supabase`). `GET /api/brand-kit` geeft de per-workspace versie terug als die
bestaat, anders het globale bestand (backward compatible voor unauth/boot). Helpers `_brand_ws_ctx` +
`_mirror_kit_to_workspace` + `_save_brand_kit`; 11 globale-save-sites omgezet.
Raakt: alleen `app.py` (brand-kit-endpoints). Cutter/export ONGEMOEID.
Risico: laag. Backup `app.py.pre-sessie74-fase1.bak` dekt ook dit (zelfde sessie).
Test (GROEN op :5599): per-workspace GET, POST->mirror->GET roundtrip, Supabase bevat de mirror, globaal
`brand_kit.json` kreeg dezelfde wijziging (cutter-bron intact), Fase-1 profielvelden bleven staan.

#### Fase 2b - jobs taggen + cutter workspace-bewust + per-workspace lokale cache (RAAKT EXPORT, checkpoint vooraf)
Wat: jobs taggen met `workspace_id` bij aanmaak (3 sites, additief zoals `user_id`). De cutter/export brand laten
lezen uit de workspace van de job (per-workspace `brand_kit.json` cache + per-workspace asset-mappen om de
vaste-bestandsnaam-clobber te vermijden), met fallback naar globaal voor oude/ongetagde jobs.
Raakt: `cutter.py` (`_load_brand_assets_for_job`) + `app.py` (job-aanmaak + `_detect_layers_for_clip` regel 6336)
+ asset-endpoint-mappen. De kroonjuwelen.
Risico: hoog. Harde CHECKPOINT met Sjuul + E2E-exporttest (echte set) voor en na.
Test: export met workspace A toont A's brand; wisselen naar B toont B's brand; geen kruisbesmetting; oude jobs
blijven werken.

### Fase 3 - Frontend per workspace
Wat: `STATE.brandKit` + de Brand Stack-view worden per workspace; artist-switchen herlaadt de brand. De nieuwe
profiel-velden (alias/cta/hashtags/caption_voice) komen in de view. Export-modal leest de actieve workspace-brand.
Raakt: `static/index.html` (Brand-view, export-modal, STATE).
Risico: middel. Frontend, met live-test per view.
Test: Brand-view toont en bewaart per artist; export-modal pakt de juiste brand.

### Fase 4 - Assets naar Supabase Storage (zwaarst, mag later/aparte sessie)
Wat: logo/fonts/watermark naar een per-workspace Storage-pad + lokale cache. Optioneel binnen deze slice; kan
als eigen vervolgstap. Tot dan blijven assets lokaal (per-workspace map uit fase 2).
Risico: middel tot hoog (binaire data + Storage-RLS). Checkpoint voor we Storage live zetten.

---

## Rollback

Per fase een backup (`app.py.pre-sessie74-faseN.bak`, `static/index.html.pre-...`). Fase 1 is puur additief
(routes verwijderen volstaat). Fase 2 is omkeerbaar door `_load_brand_kit`/`_save_brand_kit` terug te zetten naar
het globale pad. Supabase-rijen blijven staan (geen verlies).

---

## Volgorde + checkpoints

Fase 1 nu (additief, geen checkpoint). Daarna STOP voor jouw akkoord voor fase 2 (raakt export). Fase 3 na fase 2.
Fase 4 los, eventueel latere sessie. Elke backend-fase vereist een dev-server-restart om te testen
(`_dev_restart_5599.sh`).

---

## Status

Fase 1 wordt nu gebouwd (backend, niet-destructief). Backup van `app.py` vooraf. Daarna restart + live-test, dan
checkpoint voor fase 2.
