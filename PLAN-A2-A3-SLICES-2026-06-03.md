# PLAN A2/A3 (Spoor A afmaken) - slices, volgorde, risico's

Datum: 2026-06-03 (sessie 74). Status: STAPPENPLAN, nog niets gebouwd.
Bron: PLAN-COMBINED-DATA-LAYER-PLUS-ELECTRON-2026-06-02.md (v1.x), gecontroleerd tegen de echte code.
Regel: geen em-dashes/en-dashes. Per slice bouwen, testen, dan pas de volgende.

---

## Doel

A1 (multi-tenant fundament) is technisch klaar maar nog niet "aan": de backend-helpers en de
database-tabellen bestaan, maar geen enkele echte feature gebruikt ze nog. Dit plan maakt A1 af
en bouwt daar A2 (Brand per artist) en A3 (Content Calendar per artist) bovenop, in kleine
veilige stappen die de werkende analyse- en export-pijplijn niet raken.

Kernidee van de hele datalaag: media (audio + gerenderde clips) blijft lokaal op jouw Mac;
alleen lichte metadata (brand-profiel, clip-info, geplande posts) gaat naar Supabase, per artist
gescheiden. De privacy-belofte blijft dus intact.

---

## Uitgangspunt (wat staat er nu echt)

Backend (al gebouwd, additief, sessie 73):
- `_user_supabase(token)`: een Supabase-client die op naam van de ingelogde user draait, zodat de
  database-beveiliging (RLS) de echte grens tussen artists is. Niet de service-key die alles mag.
- `current_workspace_id(...)`: bepaalt welke artist actief is voor dit verzoek (leest de
  `X-Omni-Workspace`-header, checkt lidmaatschap, valt terug op de eerste artist).
- `GET /api/workspaces`: geeft de artists van de ingelogde user terug. Dit is nu de enige plek
  die de nieuwe helpers gebruikt.

Database (live op de echte server sinds sessie 71, beveiliging aan):
- Gevuld: `workspaces` + `workspace_members` (14 rijen, 1 per bestaande user).
- Leeg en klaar voor gebruik: `clips`, `dj_profiles`, `dj_templates`, `scheduled_posts`.

Frontend (gedeeltelijk, "slapend"):
- `currentWorkspaceId()` leest de sleutel `omniDjWorkspaceId` uit de browser-opslag en de
  `X-Omni-Workspace`-header zit al klaar in de centrale `api()`-aanroep plus 3 losse fetches.
- MAAR: niets vult die sleutel. De header is dus slapend en stuurt nooit een waarde.
- De artist-kiezer (de twee chips linksboven) is nog een Fase-5 nepversie: hij slaat alleen een
  weergavenaam op (`omniDjActiveArtist`), toont 2 "locked" demo-artists, en kent geen echte
  workspace-UUID's.

Brand vandaag:
- Eindpunten `/api/brand-kit*` (logo, fonts, watermark, presets) op EEN globaal bestand
  `brand_kit.json` (via `_load_brand_kit`/`_save_brand_kit`). Niet per artist gescheiden.

Calendar vandaag:
- De Calendar-view (sessie 56) is een werkende schil op browser-opslag (localStorage). Drafts
  overleven een refresh, maar niet een herinstallatie en zijn niet per artist gescheiden.

Openstaand opruimpunt:
- Migratie 010 (verplaatst beveiligingshelpers naar een apart schema, ruimt 3 advisor-waarschuwingen
  op). Alleen review, nog niet toegepast. Niet nodig om A2/A3 te laten werken, wel nettere afsluiting.

---

## De slices (in aanbevolen volgorde)

Per slice: wat het doet, wat het raakt, het risico, en hoe we het testen.

### Slice 1 - Workspace-header activeren (het scharnierpunt)

Wat: de artist-kiezer koppelen aan `GET /api/workspaces`. Na inloggen halen we de echte artists op,
zetten we de actieve workspace-UUID in `omniDjWorkspaceId`, en vullen we de chip plus de dropdown
met echte namen in plaats van de nepversie. Standaard = de primaire artist.

Effect: de slapende `X-Omni-Workspace`-header gaat in een klap end-to-end werken, en
`current_workspace_id()` op de server lost vanaf nu een echte artist op. Dit is letterlijk "A1 aanzetten".

Raakt: alleen `static/index.html` (frontend). De backend is al klaar. Analyse, export en auth blijven
ongemoeid.

Risico: laag. Additief, omkeerbaar, geen databasewijziging. Valkuil: de oude sleutel
`omniDjActiveArtist` (weergavenaam) en de nieuwe `omniDjWorkspaceId` (UUID) niet door elkaar halen.

Test (op de Mac, op :5599, ingelogd): de chip toont je echte artistnaam; in de console geeft
`/api/workspaces` alleen jouw artist(s) terug (niet alle 14); een willekeurige authed-aanroep stuurt
nu de `X-Omni-Workspace`-header mee. Kernflow (analyse, editor, export) blijft groen.

### Slice 2 - Brand-profiel per artist (A2, eerste echte content-data)

Wat: een brand-profiel per artist opslaan en lezen uit `dj_profiles` (1 rij per workspace, een
`profile`-blob met visual/typografie/lower-third/cta/hashtags/caption-voice). Nieuwe eindpunten die
via `_user_supabase` + `current_workspace_id` lopen, zodat artist A nooit het profiel van B ziet.
Het bestaande globale `brand_kit.json` wordt eenmalig naar het profiel van de standaard-artist
gemigreerd. De bestaande Brand-view (de "Brand Stack") wordt hierop omgelegd, niet gedupliceerd.

Effect: dit is de eerste echte WRITE door de RLS-laag, het bewijst de hele multi-tenant-opzet met
echte data.

Raakt: `app.py` (nieuwe brand-profiel-eindpunten naast de bestaande `/api/brand-kit*`) en
`static/index.html` (Brand-view leest/schrijft het profiel). Assets (logo/fonts/watermark) blijven
in deze slice nog op de bestaande lokale opslag; alleen de metadata gaat naar Supabase.

Risico: middel. Aandachtspunten: de bestaande `/api/brand-kit*`-flow niet breken tijdens het omleggen,
en de eenmalige migratie van `brand_kit.json` zorgvuldig doen. Klein bijvangst-punt: er staan nu
dubbele route-definities voor `/api/brand-kit/logo` (regel 3042 en 5915); die check ik hierbij meteen.

Test: profiel opslaan als artist A, wisselen naar artist B, B ziet A's profiel niet. Bestaand
lokaal brand-kit is correct overgezet naar het standaard-profiel.

### Slice 3 - Brand toepassen in de render (A2, renderer-uitbreiding)

Wat: de clip-renderer (`cutter.py`) het profiel plus een gekozen template laten toepassen
(logo-overlay, lower-third, cta, hashtags) bij export. Beginnen met EEN template ("Festival-clip"),
daarna 1 tot 2 dagen per extra template.

Raakt: `cutter.py` (de werkende drawtext/caption-pijplijn UITBREIDEN, niet herschrijven) plus de
export-flow die het actieve template meegeeft.

Risico: hoger. Dit zit in de render-pijplijn die nu werkt (captions, sessie 50 en 67). Daarom een
aparte slice met backup en een E2E-exporttest voor en na.

Test: export met profiel toegepast toont logo plus lower-third plus cta. Een export zonder profiel
blijft werken zoals nu.

Opmerking: Slice 3 mag later. Slice 1 plus 2 leveren al een per-artist brand-profiel; de render-toepassing
is een losse vervolgstap.

### Slice 4 - Content Calendar per artist (A3)

Wat: de Calendar-schil van browser-opslag omzetten naar `scheduled_posts` in Supabase, per artist
gescheiden. Nieuwe eindpunten (lijst/plan/wijzig/verwijder) via de RLS-laag. Plus een "Plan in
Calendar"-knop in de export-modal (datum/tijd, platform-keuze, caption voorgevuld met het clip-label).
Publiceert niets; puur een draft-systeem.

Raakt: `app.py` (nieuwe calendar-eindpunten) en `static/index.html` (Calendar-view en export-modal).
Het bestaande visuele werk blijft; alleen de databron wisselt.

Risico: middel. Open ontwerppunt: `scheduled_posts.clip_id` verwijst naar een `clips`-rij, maar clips
leven nu lokaal. In het schema is `clip_id` optioneel, dus drafts kunnen eerst zonder een clips-rij;
of we vullen lichte clip-metadata in `clips`. Dat beslissen we aan het begin van deze slice.

Test: post gepland bij artist A is onzichtbaar bij artist B. Een draft overleeft een herinstallatie
(staat in Supabase, niet in de browser). "Plan in Calendar" vanuit export maakt een echte rij.

### Slice 5 - Pijplijn-koppelingen + per-artist mappen (Correctie 8)

Wat: voordat we de lokale media per artist in aparte mappen zetten, eerst de plekken afdichten die
nu blind door de hele `OUTPUT_DIR` lopen: history en export-overzichten (regels 394, 4452, 4487, 6858
in `app.py`). Anders mengt of verdwijnt data zodra er per-artist-submappen komen.

Raakt: `app.py` (de genoemde sweep-plekken) en de map-structuur voor lokale opslag.

Risico: middel tot hoog, want het raakt waar clips op schijf staan. Daarom expliciet als laatste,
met een duidelijke test op bestaande sets.

Belangrijk: dit is alleen nodig voor de LOKALE per-artist mappen. De Supabase-metadata uit Slice 2 en
4 heeft Slice 5 niet nodig. We kunnen Slice 1 tot 4 dus volledig afronden voordat Slice 5 aan de beurt is.

### Los punt - Migratie 010 (opruiming, optioneel)

Wat: beveiligingshelpers naar een apart schema verplaatsen om de laatste 3 advisor-waarschuwingen op
te lossen. Laag risico, niet nodig voor A2/A3.

Aanpak: eerst op een wegwerp-branch toepassen, cross-account-audit opnieuw draaien, en pas daarna met
jouw akkoord op de hoofd-database. Dit is een van de vaste checkpoints (zie onder).

---

## Volgorde en afhankelijkheden

- Slice 1 eerst. Alles hangt eraan (zonder actieve workspace heeft per-artist-data geen anker).
- Slice 2 na 1. Dan Slice 3 na 2 (of later; Slice 3 is uitstelbaar).
- Slice 4 kan na Slice 1, eventueel parallel aan Slice 2/3. Aanbeveling: Slice 2 eerst, want de
  Calendar-previews tonen straks de brand op de clip.
- Slice 5 als laatste, vlak voordat lokale per-artist mappen live gaan.
- Migratie 010 wanneer het uitkomt, los van de slices, altijd met checkpoint.

Tijdsindicatie uit het combinatie-plan (ruw): A2 ongeveer 2 weken plus 1 tot 2 dagen per extra
template; A3 ongeveer 2 tot 3 weken. Per slice is het behapbaar; in totaal is dit weken werk, geen
enkele sessie.

---

## Risico's en hoe we ze afdekken

- Data lekt tussen artists. Afdekking: alle content-queries via `_user_supabase` (niet de service-key),
  en na elke data-slice een cross-account-test (A ziet 0 van B, beide richtingen).
- De werkende render-pijplijn breekt (Slice 3). Afdekking: aparte slice, backup vooraf, E2E-export voor
  en na, beginnen met 1 template.
- Lokale mappen door elkaar (Slice 5). Afdekking: eerst de sweep-plekken afdichten, dan pas verplaatsen,
  testen op bestaande sets.
- Scope-creep. Afdekking: strikt per slice, niets "meteen even meenemen", Postiz/echte publicatie en ads
  blijven buiten dit plan.

---

## Checkpoints (waar ik op "ja" wacht)

1. Voor elke database-wijziging op de hoofd-server (bijvoorbeeld migratie 010): eerst branch plus audit,
   dan jouw akkoord.
2. Voor bestandsverwijdering of het verplaatsen van bestaande lokale clips (Slice 5).
3. Voor een commit plus gesignde rebuild plus DMG naar R2 (en die rebuild pas na de picker-smoketest,
   harde regel uit de HANDOVER).

Binnen een slice (frontend, additieve eindpunten) bouw en test ik door zoals afgesproken; ik meld als
de scope groter blijkt dan hier beschreven.

---

## Buiten scope (nu niet bouwen)

Echte publicatie naar TikTok/Instagram (Postiz/OAuth), het ads-systeem, Spoor B (Electron), Spoor C
(redesign van de views), Spoor D (audio-sync), en de effecten-spec. Die staan in het combinatie-plan
en komen later aan bod.

---

## Voorstel voor de eerstvolgende stap

Beginnen met Slice 1 (workspace-header activeren). Frontend-only, laag risico, en het zet A1 in een
klap "aan" zodat alle volgende slices een echte artist hebben om data aan te hangen. Zeg "ja" en ik
maak een backup, bouw Slice 1, en test op :5599.
