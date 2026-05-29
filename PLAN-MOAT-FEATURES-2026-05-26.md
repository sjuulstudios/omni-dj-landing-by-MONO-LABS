# Omni DJ — Moat-features & Ad-spend platform plan

> **Versie:** 1.0 — 2026-05-26
> **Auteur:** Claude + Sjuul (sessie na compactie)
> **Status:** Strategisch + technisch plan. Nog niet bouwen — eerst lezen, daarna prioriteren.
> **Reikwijdte:** Features 5 (multicam), 7 (branding), 8 (auto-draft/publish + content calendar), 9 (privacy/on-device als premium) en de ad-spend-as-a-service laag (Intellijend-model).

---

## 0. Waarom dit plan bestaat

Er komen steeds krachtigere generieke AI video-agents (OpusClip, HeyGen Agent, Premiere AI, en straks Google/OpenAI video-agents) die op basis van een simpele prompt video's kunnen editen. De vraag is: **waarom zou een DJ over 6–24 maanden nog Omni DJ kiezen?**

Het antwoord is niet "we knippen op drops" — dat doet iedereen straks. Het antwoord moet zijn:

1. We doen DJ-specifieke dingen die generieke agents nooit goed zullen doen.
2. We werken structureel anders (lokaal, watch-folder, geen upload-limiet).
3. We sluiten de hele waardeketen: van set-opname → clips → publiceren → adverteren → analyseren.

Dit plan beschrijft hoe punt 1 (#7 branding) + punt 2 (#9 lokaal) + de auto-publish pipeline (#8) + de ad-spend laag (Intellijend-model) samen één geïntegreerd product worden waar geen agent op kan concurreren.

Feature #5 (multicam) blijft op de roadmap maar krijgt in dit plan minder gewicht — eerst de drie structurele pilaren.

---

## 1. De strategische logica — hoe versterken de features elkaar

Het komt erop neer dat elke feature de volgende feature waardevoller maakt. Een DJ kan op één plek instappen, maar zodra hij eenmaal binnen is, wordt elke volgende stap aantrekkelijker.

```
[#9 Lokaal/Privacy]  →  vertrouwen: "mijn unreleased ID's blijven op mijn Mac"
        ↓
[#7 Branding profiel]  →  consistentie: elke clip ziet er hetzelfde uit
        ↓
[#8 Auto-draft pipeline]  →  schaal: 30 clips/week zonder werk
        ↓
[Content calendar]  →  ritme: posts staan klaar, DJ ziet wat wanneer gaat
        ↓
[Ad-spend platform]  →  bereik: dezelfde clips worden automatisch getest + opgeschaald
        ↓
[Analytics terug naar #7 en #8]  →  leren: welke branding/template/clip-type performt
```

De waarde van dit alles bij elkaar is groter dan de som van de delen. Een agent die alleen clips knipt heeft geen profiel, geen calendar, geen ad-spend, geen leerlus. Daar zit de moat.

Concreet voorbeeld van versterking:

- De ad-spend module heeft pas écht waarde als er **veel clips** zijn om te testen. Dat krijg je van de auto-draft pipeline.
- De auto-draft pipeline heeft pas waarde als de clips er **professioneel uitzien**. Dat krijg je van het branding profiel.
- Het branding profiel werkt pas als de DJ **niet bang is** om materiaal te uploaden. Dat krijg je van lokaal/privacy.
- De ad-spend resultaten **verbeteren** het branding profiel en de auto-draft regels. Dat is de leerlus.

Een losse OpusClip-knipper of een Premiere-template heeft geen van deze koppelingen.

---

## 2. Feature 9 — Lokaal & Privacy als premium positioning

### Waarom dit eerst

Dit is geen feature die je bouwt, dit is **een positionering die je expliciet maakt**. Omni DJ draait al lokaal. Wat ontbreekt is dat we het *verkopen* als zodanig en er een paar concrete privacy-waarborgen omheen bouwen die je kunt aantonen en uitleggen.

### Wat er concreet aan bestaat

Vanuit de huidige codebase (memory + handover):

- Lokaal draaiende Flask + ffmpeg, audio-analyse via librosa op de machine van de gebruiker.
- Native file picker werkt voor elke bestandsgrootte (sessie 39).
- `.app` build bestaat (open bug: ffmpeg-pad in bundle, eerst oplossen).

### Wat we daar nog aan toevoegen

**A. Tier 3: "Studio" — alles blijft lokaal**

Premium tier waarin we expliciet garanderen:

- Geen audio of video upload naar onze server.
- Geen telemetry behalve geanonimiseerde usage stats (en opt-out).
- Geen 3rd-party AI services worden aangeroepen voor analyse — alles draait op de machine.
- Optionele "airgap mode" — alle outbound network calls behalve license check geblokkeerd via een schakelaar in settings.

Dit is voor headliners die unreleased ID's draaien en zenuwachtig worden van elke upload. Hogere prijs (zie sectie 9).

**B. Cryptografisch attest van lokale verwerking**

Bij elke geanalyseerde set genereren we een lokaal logbestand `clip-live-attest-{set-id}.json` met:
- Tijdstempel
- SHA-256 van het bron-bestand
- Bevestiging "audio analyzed locally, no upload"
- Lijst van uitgaande connecties tijdens analyse (mag leeg zijn)
- Versie van de app + ffmpeg

Dat is geen rocket science maar het is wel iets dat een DJ in zijn contract met een label of een agency kan tonen als bewijs van zorgvuldigheid. Geen cloud-tool kan dit aanbieden.

**C. Marketing-pagina "Where your music goes"**

Eén pagina op de site met een dataflow-diagram: audio-bestand → librosa lokaal → ffmpeg lokaal → clips lokaal opgeslagen. Géén pijl naar buiten behalve "license check" en optioneel "social media post via API".

### Bouwwerk

- Schakelaar "airgap mode" in settings (1 dag werk, blokkeert outbound via simpele firewall-rules of Python-level requests-blok).
- Attest-generator (halve dag, schrijft JSON bij elke analyse).
- Marketing-pagina (los, niet in scope van dev-werk).

### Risico's

- "Lokaal" verbiedt cloud-features. Als we later cloud-rendering willen aanbieden voor snelheid, moet die los staan en niet stilzwijgend de privacy-belofte breken. Tier-grens helder houden.
- Het attest is alleen geldig als de app het ook waarmaakt. Bij elke release een kleine audit doen dat er geen ongewenste outbound calls bij zijn gekomen.

---

## 3. Feature 7 — Branding profielen per DJ

### Waarom dit in Omni DJ thuishoort en niet in Premiere

Je vraag was terecht: een vast template met fonts, logo en kleuren kan ook in Premiere als preset. Dat klopt — voor één DJ die zijn eigen workflow opbouwt.

Het verschil: in Omni DJ is het **een first-class profiel dat overal automatisch wordt toegepast**, niet een handmatige preset die je per project moet laden. En het profiel werkt mee in de ad-spend module, in de auto-draft pipeline, in de content calendar. Premiere weet niet wat een "DJ-persona" is, kent geen Spotify-link variabele, weet niet dat hashtags per platform anders zijn.

Dus: Premiere heeft templates. Omni DJ heeft een **DJ-identity profile** dat door alle features heen wordt geweven.

### Wat een profiel bevat

```yaml
dj_profile:
  artist_name: "DJ Sjuul"
  alias: "@sjuulstudios"
  
  visual:
    logo: path/to/logo.png  # transparante PNG
    logo_position: bottom_right
    logo_size: 8%  # van frame-hoogte
    primary_color: "#FF3D00"
    secondary_color: "#000000"
    accent_color: "#FFFFFF"
    
  typography:
    title_font: "Inter Bold"
    caption_font: "Inter Regular"
    caption_style: "two_word_punch"  # of "lyric_sync", "minimal", "festival"
    
  lower_third:
    enabled: true
    template: "name_below_logo"
    duration: 3.0  # seconden vanaf clip-start
    
  cta:
    style: "out_now"  # of "stream_now", "coming_soon", "save_the_date"
    spotify_link: "spotify:artist:..."
    beatport_link: "..."
    show_in_last_seconds: 2.5
    
  hashtags:
    tiktok: ["#djset", "#techno", "#yourtag"]
    instagram: ["#djlife", "#techno", "#yourtag"]
    youtube_shorts: ["#shorts", "#djset", "#techno"]
    
  caption_voice:
    tone: "hyped"  # of "minimal", "informative", "ironic"
    use_emojis: true
    max_length_chars: 80
```

### Profielen vs. templates

Een profiel kan **meerdere templates** hebben voor verschillende contexten:

- "Festival-clip" template — hardere captions, festival-hashtags, "live at" lower-third
- "Studio-mix" template — softer, minder hashtags, "available on Spotify" CTA
- "Track-release" template — track-naam prominent, release-datum CTA
- "Behind-the-scenes" template — geen drop-focus, ander tempo

De DJ kiest niet per clip welk template — de pipeline kiest op basis van **context-tags** die hij bij upload meegeeft (of automatisch worden gedetecteerd: festival vs. studio op basis van crowd-detectie).

### Bouwwerk

Op de huidige stack:

- Tabel `dj_profiles` in Supabase: één per user, JSON-blob met bovenstaande structuur.
- Tabel `dj_templates`: meerdere per profiel, met overschrijvende velden.
- Upload-flow voor logo's via Supabase storage (versleuteld bucket, alleen eigenaar leest).
- Editor-UI in de bestaande "Brand Stack" sectie van index.html (al deels gebouwd volgens sessie 30).
- Renderer in `cutter.py` die het profiel + template leest en in ffmpeg-filter syntax toepast (drawtext, overlay, fade).

Geschatte werk: 2 weken voor profiel-CRUD + renderer + één template (festival-clip). Daarna 1–2 dagen per extra template.

### Versterking met andere features

- Auto-draft pipeline (#8) gebruikt het profiel automatisch — geen handmatige stap meer.
- Ad-spend module gebruikt de profiel-hashtags en CTA's voor ad-creatives.
- Content calendar toont previews met het profiel toegepast.

---

## 4. Feature 8 — Auto-draft pipeline + Content calendar + Watch folder

### De pitch in één zin

"DJ uploadt zijn set naar zijn watch folder. De volgende ochtend staan er 10 clips klaar — gebrand, met captions, op zijn content calendar gepland voor de komende 2 weken — wachtend op één goedkeuring per clip in de mobiele app."

### Architectuur — drie lagen

**Laag 1: Watch folder + ingest**

- DJ wijst in settings één of meerdere folders aan: lokale Dropbox-sync, Google Drive desktop-sync, of gewoon een lokale folder.
- Een fswatch/watchdog proces draait als achtergrond-service van Omni DJ.
- Nieuwe video- of audio-bestanden boven X minuten lang (instelbaar, default 20 min) worden automatisch in de queue gezet.
- Er is ook een "manual override" — DJ kan een bestand handmatig naar de queue slepen.

Technisch:

- Op macOS: `fswatch` via subprocess of native `watchdog` Python library.
- Queue in SQLite (lokaal) — niet Supabase, want het is lokale state.
- Bij detectie: filemetadata + hash opslaan, dan analyse-job triggeren.

**Laag 2: Auto-draft generator**

Voor elke set in de queue:

1. Lees DJ-profiel + actieve template.
2. Detecteer drops (huidige analyzer.py).
3. Maak N clips (configureerbaar, default 8–12 per set).
4. Render elke clip in 3 formats: 9:16 (TikTok/Reels), 1:1 (feed), 16:9 (YouTube).
5. Genereer captions per platform (zie hieronder).
6. Sla op in `~/Library/Application Support/Omni DJ/drafts/{set-id}/`.
7. Upload preview-thumbnails naar Supabase storage (niet de volledige video — die blijft lokaal).
8. Maak entries in `pending_clips` tabel: `{user_id, clip_id, set_id, suggested_post_time, platform_targets, status: 'pending_review'}`.

Caption-generatie: Gebruik een lokale LLM (Ollama met Llama 3.1 8B) of optioneel via cloud API (alleen op tier "Pro" of "Plus" — niet "Studio"). Caption-stijl uit profiel.

**Laag 3: Content calendar + approval flow**

In de web-app:

- Kalenderview (week/maand) met posts voorgesteld door de tool.
- Per voorgestelde post: thumbnail, caption, platform, voorgestelde tijd.
- DJ kan: goedkeuren (1 tap), aanpassen, verschuiven, of weggooien.
- Posting-tijden: standaard suggestie op basis van platform-best-practices per genre, later op basis van DJ's eigen analytics.
- Bulk-approve knop: "goedkeur alle clips uit set X met huidige instellingen".

Mobile companion app (later — niet voor v1):
- Push-notificatie: "5 nieuwe drafts wachten op je goedkeuring".
- Swipe-interface: swipe right = approve, swipe left = skip, tap = edit.

### Direct publishing — wat kan en wat niet

Op basis van research naar API's per platform:

| Platform | Direct publish mogelijk? | Eisen | Aanpak |
|---|---|---|---|
| YouTube Shorts | Ja, via YouTube Data API v3 | OAuth, weinig friction | **Phase 1** — direct publish |
| Instagram Reels | Ja, via Meta Graph API | Business account, App Review, Meta-verificatie (kan weken duren) | **Phase 2** — start met draft-to-mobile, daarna direct publish |
| TikTok | Ja, via Content Posting API | OAuth + App Review met demo-video, geen watermarks, verplichte UI-elementen (privacy selector, duet/stitch toggles), max 15 posts/dag/creator | **Phase 2** — App Review traject parallel starten |
| SoundCloud / Mixcloud | Beperkt (geen video) | Eigen API per platform | **Phase 3** — alleen audio-clips |

**Belangrijk juridisch/operationeel:**

- TikTok eist een werkende demo-video van de upload + OAuth flow als onderdeel van App Review. Begin dit traject zodra de pipeline werkt — review duurt 2–6 weken.
- Meta Marketing API (voor ad-spend) heeft **Advanced Access** nodig — apart traject, ook weken.
- App Review voor beide is onvermijdelijk als je multi-tenant wilt zijn. Niet uitstelbaar.

### Auto-publish vs. auto-draft — beide aanbieden

Niet één of het ander. Twee modes:

- **Auto-draft** (default voor nieuwe users) — clips komen klaar, DJ keurt elk goed.
- **Auto-publish** (opt-in, met confidence-threshold) — clips boven een bepaalde "quality score" worden direct gepost zonder approval. DJ stelt eigen drempel in. Standaard alleen voor TikTok+YouTube, niet Instagram (review-risico hoger).

Voor "auto-publish" moet er een **veiligheidsklep** zijn:
- Max 3 auto-publishes per dag per platform (anti-spam).
- Kill-switch in de app om alle auto-publishes te pauzeren.
- Elke auto-publish krijgt 30 minuten "annuleer-venster" waarin DJ via push-melding nog kan intrekken.

### Wat heb ik van jou nodig om dit te bouwen

Concrete inputs:

1. **Eén volledig branding-profiel van jezelf** als test-DJ — logo, kleuren, fonts, voorbeeld-CTA's, voorbeeld-hashtags voor alle drie de platforms. Anders bouwen we in het luchtledige.
2. **5 voorbeeld-sets** (ze hoeven niet 7GB te zijn, 30-min sets is genoeg) met variatie: techno, house, festival-recording, studio-mix, etc. Zo kunnen we de pipeline end-to-end testen.
3. **Eén Instagram business account, één TikTok account, één YouTube channel** waarmee we de OAuth-flows kunnen testen tijdens dev. Hoeven niet jouw productie-accounts te zijn — een test-set is veiliger.
4. **Een Meta Business Manager met business verification gestart** — dit is de gating-stap voor zowel Instagram publishing als ad-spend. Begin zo vroeg mogelijk, kan 1–4 weken duren.
5. **Beslissing over tier-naming en prijs** — zonder dat kunnen we de upgrade-flows in de UI niet bouwen. Voorstel in sectie 9.
6. **Eén dag van jezelf** voor het invullen van content-calendar-defaults: "wat is een goede posting-tijd voor een Nederlandse techno-DJ op TikTok?". Dat soort vraag-werk dat alleen jij kunt beantwoorden.

Niet meteen nodig (komt later):

- App Store / TestFlight voor de mobile companion app — phase 3.
- Domeinnamen voor publieke landing pages — kan later.

### Werk-schatting

- Watch folder + queue: 1 week.
- Auto-draft generator op bestaande analyzer/cutter: 1–2 weken.
- Caption-generatie met lokale LLM: 1 week (Ollama install + prompt-engineering).
- Calendar UI: 2 weken.
- Approval flow + edit UI: 1 week.
- YouTube Shorts publish: 1 week.
- Instagram Reels publish + App Review prep: 2 weken werk + 2–6 weken wachten op review.
- TikTok publish + App Review prep: 2 weken werk + 2–6 weken wachten.
- Auto-publish veiligheidsklep + push notifications: 1 week.

**Totaal: 12–14 weken dev** + reviews parallel. Realistisch een kwartaal hard werken.

---

## 5. Ad-spend platform — het Intellijend-model voor DJs

### Wat Intellijend doet

Onderzoek bevestigt: Intellijend koppelt het Meta Ad account van een artiest aan een interne automatiseringslaag, beheert "Front-Loaded" of "Steady State" budgetten, schakelt slecht-presterende ad-sets automatisch uit, herverdeelt budget naar winnaars. Pricing: ~$25/maand SaaS-fee bovenop wat de artiest zelf aan Meta betaalt (ad spend gaat dus rechtstreeks naar Meta).

### Hoe wij het voor DJ-video's doen — gespecialiseerd, niet generiek

Intellijend is gericht op Spotify-streams. Wij zijn gericht op **DJ-content engagement én Spotify-streams** (want elke DJ wil uiteindelijk dat zijn tracks gestreamd worden). Onze unfair advantage: wij hébben de creatives al, want de auto-draft pipeline maakt ze.

Een Intellijend-gebruiker moet zelf 5–10 ad-creatives aanleveren. Een Omni DJ-gebruiker heeft er per set 10. **Dat is een fundamenteel andere positie.**

### Hoe het technisch werkt — eindgebruiker perspectief

1. DJ koppelt zijn Meta Business Manager + ad account via OAuth (vereist business verification, zie sectie 4).
2. DJ koppelt zijn Spotify-artist-profiel (Spotify for Artists OAuth).
3. DJ stelt in: maandelijks ad-budget (bv. €300), doel ("groei volgers", "stream-conversie", "event-tickets verkopen", "mailinglijst opbouwen"), regio (NL, EU, wereldwijd).
4. Omni DJ's ad-engine pakt automatisch:
   - De 10 clips van zijn laatste set.
   - Maakt per clip een ad-creative variant (verschillende thumbnails, captions, korte vs. lange versie).
   - Lanceert een test-campagne in Meta Ads Manager met klein budget per variant (€2–5/dag).
   - Na 48u: kill de slechtste 50% qua CTR / cost-per-result. Verdeel budget over de winnaars.
   - Na 7 dagen: schaal de top-2 op tot 60% van het budget. Houd 20% experimenteel voor nieuwe varianten.
5. DJ ziet een dashboard: hoeveel nieuwe volgers, hoeveel streams, cost-per-result.

### Hoe het technisch werkt — bouwlaag

**Meta Marketing API integratie**

Vereisten (uit research):
- Eigen Meta App in Developer portal met "Marketing API" product enabled.
- Advanced Access op alle relevante permissions (`ads_management`, `ads_read`, `business_management`, `pages_read_engagement`).
- App Review met use-case "managing ads on behalf of music artists for their own ad accounts".
- OAuth-flow waarin DJ Omni DJ explicit toestaat zijn ad account te beheren.

**Engine-architectuur (server-side, op Supabase Edge Functions + een aparte Node service voor de orchestrator)**

```
[Omni DJ local app]
    ↓ (clips + branding + targets)
[Supabase API]
    ↓ (jobs)
[Ad Orchestrator Service]  ← runs op een goedkope VPS of Render
    ↓ (campagne-acties)
[Meta Marketing API]
[Spotify for Artists API]  ← voor measurement
    ↓ (resultaten)
[Supabase analytics tables]
    ↓
[Omni DJ dashboard]
```

Belangrijke beslissing: de orchestrator is een aparte service, niet onderdeel van de lokale Mac-app. Want hij moet 24/7 draaien om ad-sets aan te passen. De **clips zelf** blijven lokaal — alleen de gerenderde MP4 wordt naar Meta gepusht via hun standaard upload-endpoint, exact zoals een gewone Ads Manager dat ook doet. Geen extra data-deling.

**Optimalisatie-logica**

Begin simpel — geen ML. Heuristieken op CTR, CPM en cost-per-result:

```python
# pseudo
def daily_optimization(campaign):
    ad_sets = meta_api.get_ad_sets(campaign.id)
    age_hours = (now - campaign.created).hours
    
    if age_hours < 48:
        return  # learning phase, niets doen
    
    sorted_by_cpr = sorted(ad_sets, key=lambda a: a.cost_per_result)
    
    if age_hours < 168:  # eerste week
        # kill onderste 50%
        for ad_set in sorted_by_cpr[len(sorted_by_cpr)//2:]:
            if ad_set.cost_per_result > campaign.target_cpr * 1.5:
                meta_api.pause(ad_set.id)
    else:
        # schaal top 2
        winners = sorted_by_cpr[:2]
        for w in winners:
            new_budget = min(w.budget * 1.3, campaign.max_daily / 2)
            meta_api.update_budget(w.id, new_budget)
```

Later: vervang heuristieken door iets adaptiever (Thompson sampling op multi-armed bandit), maar pas als we 50+ campagnes hebben om van te leren.

**Spotify measurement**

Spotify for Artists API geeft access tot stream-counts, save-rate, follower-growth per dag. Door dit te correleren met ad-spend per dag krijgen we een **echte ROI** — niet alleen "video views" maar "streams per €". Dat is het verkoopargument.

### Pricing-model — twee opties

**Optie A: SaaS-fee bovenop ad-spend (Intellijend-model)**

- DJ betaalt €X/maand voor Omni DJ Plus (met ad-engine).
- DJ's ad-budget gaat rechtstreeks naar Meta (wij raken het niet aan).
- Wij verdienen alleen aan de SaaS-fee.
- Voordelen: simpel, transparant, geen financieel risico voor ons.
- Nadelen: we missen de "schaalvoordelen" — als een DJ €5000/maand uitgeeft, krijgen wij nog steeds maar €X.

**Optie B: SaaS-fee + percentage van ad-spend (agency-model)**

- DJ betaalt €X/maand basis-tarief.
- + 10% van zijn maandelijkse ad-spend, gefactureerd via Omni DJ.
- Het ad-budget loopt **via ons** — wij ontvangen €Y, geven daarvan €Y × 0.91 aan Meta, houden 9% over.
- Voordelen: schaalbare inkomsten, lijkt op hoe ad-agencies werken.
- Nadelen: complexiteit (we hanteren geld dat niet van ons is — boekhoudkundig en juridisch zwaarder), DJ kan switchen naar zelf-managen om de 10% te besparen.

**Mijn aanbeveling: Optie A voor v1, Optie B als premium "Managed" tier later.**

Reden: optie A is in 4–6 weken bouwbaar, optie B is een ander juridisch beest (we worden dan in NL waarschijnlijk een "betaaldienstverlener" of hebben PSP-vergunning nodig). Begin met SaaS, voeg "Managed" later toe voor DJ's die €1000+/maand uitgeven.

### Risico's

- **Meta App Review afwijzing.** Reden om bang voor te zijn: ze accepteren niet zomaar een tool die "ads voor andere accounts beheert". Mitigatie: positioneer als "self-service tool for artists managing their own ad account" — niet als agency-tool. Lever schone demo-video.
- **API-changes.** Meta API verandert frequent. Plan onderhouds-uren in.
- **Slechte campagnes = teleurgestelde DJ.** Verwachtingsmanagement is cruciaal. Toon expliciet de baseline van wat realistisch is (cost-per-follower in NL techno is typisch €0.30–€1.20). Geen "viral guarantees".
- **Wettelijke disclosure.** EU heeft transparantie-eisen voor geautomatiseerde advertising. Documenteer in T&C dat we Meta's targeting gebruiken en hoe.

### Wat heb ik van jou nodig

1. **Meta Business Manager + business verification gestart** (zoals in sectie 4, dit is dubbel-gebruikt).
2. **Eén echt ad-budget om mee te testen** — €200–€500 over een maand voor jouw eigen DJ-set. Dan kunnen we de pipeline end-to-end echt valideren met echte data, niet in een sandbox.
3. **Spotify for Artists toegang** voor je eigen profiel als je een artiest hebt, of een bevriende DJ die dit wil testen.
4. **Beslissing pricing-model A vs. B** zodra de basis er staat.

### Werk-schatting

- Meta API auth + campagne-creatie + creative upload: 3 weken.
- Orchestrator service (Node + Postgres of Supabase): 2 weken.
- Spotify-koppeling + analytics: 1 week.
- Dashboard in app: 2 weken.
- App Review traject: 2 weken werk + 2–6 weken wachten.

**Totaal: 8–10 weken dev** + review-wachttijd.

---

## 6. Feature 5 — Multicam (lagere prioriteit, blijft op de roadmap)

Op basis van jouw input — feedback dat de tool niet kan bepalen of DJ zichzelf of het publiek wil zien — kiezen we de twee acceptabele paden:

- **Optie B: Beide versies genereren.** Voor elke drop maakt de tool zowel een crowd-cut als een DJ-cut. DJ kiest in approval-flow.
- **Optie C: Mobile push-notificatie per clip.** Toont 2 thumbnails, DJ tikt voorkeur. Voegt 30 sec toe per clip.

Implementatie-aanpak:

1. Multicam-sync (audio-waveform alignment via ffmpeg `silenceremove` + cross-correlation) — best-of-breed open source bestaat (PluralEyes-achtig).
2. Detectie van shot-type via simpele CLIP-classifier: "wide crowd", "DJ face", "DJ hands", "lights/laser", "atmosphere".
3. Per clip: render één crowd-variant en één DJ-face-variant, breng beide in de approval flow.

**Werk:** 3–4 weken na dat #7 en #8 staan. Niet eerder beginnen.

---

## 7. Volgorde + roadmap (gecombineerd)

```
[Maand 1]   Fix .app build (open bug uit sessie 39)
            Feature #9 implementatie (airgap mode + attest + marketing-pagina)
            Feature #7 branding profielen — schema + één template
            Meta Business Manager verification starten (parallel)
            TikTok developer account aanvragen (parallel)

[Maand 2]   Feature #7 — 3 templates klaar
            Feature #8 — watch folder + auto-draft generator
            Caption-generatie met Ollama
            YouTube Shorts publishing

[Maand 3]   Feature #8 — calendar UI + approval flow
            Instagram Reels publishing
            Meta Marketing API integratie startfase
            TikTok App Review submitten

[Maand 4]   Ad-spend orchestrator service
            Spotify-koppeling
            Dashboard
            TikTok publishing live (na review)
            Meta App Review submitten

[Maand 5]   Auto-publish veiligheidsklep
            Ad-spend live voor early testers
            Feature #5 multicam in dev

[Maand 6]   Mobile companion app eerste versie
            Feature #5 multicam live
            "Managed" tier (optie B pricing) onderzoek
```

Dit is **agressief** maar haalbaar als jij niets anders gaat doen. Realistisch: 8–10 maanden tot alles in een goede staat is.

---

## 8. Tier-structuur — voorstel

| Tier | Naam (werkbenaming) | Prijs/mnd | Voor wie | Wat erin zit |
|---|---|---|---|---|
| Free | Starter | €0 | Test | 3 clips/maand, watermark, geen profielen |
| Tier 1 | Clip | €19 | Hobby DJ | Onbeperkt clips lokaal, 1 branding profiel, manual export, geen direct publish |
| Tier 2 | Stage | €49 | Pro DJ | Watch folder + auto-draft, content calendar, direct publish naar 3 platforms, 3 profielen |
| Tier 3 | Studio | €99 | Headliner | Alles van Stage + airgap mode + attest + prioritaire support |
| Tier 4 | Stage + Ads | €69 | Pro DJ met budget | Stage + ad-spend module (eigen budget naar Meta) |
| Tier 5 | Managed | 10% + €99 basis | DJ met €1000+ ad-budget | Studio + we beheren ad-budget |

Deze prijsstructuur stemt overeen met wat in de memory staat over Omni DJ/Live (~paid architecture, Stripe-integratie). De ad-spend tier zit bewust **lager** dan Studio: ad-spend is voor pro maar geen privacy-paranoide, Studio is voor de bovenste 5% die unreleased ID's draaien.

---

## 9. Wat er aan dit plan ontbreekt en wat we expres niet meenemen

Eerlijk zijn over scope:

- **Geen mobile app spec.** Komt later, eerst de pipeline werkend.
- **Geen detail op caption-LLM prompt engineering.** Wel architectuur, geen exacte prompts — die maken we tijdens bouwen.
- **Geen multitenancy + team-accounts.** Voor labels die meerdere DJs beheren — interessante tier-uitbreiding maar later.
- **Geen detail op TikTok-specifieke UX-rules** (privacy selectors, branded content toggles) — staat globaal in sectie 4, detail komt tijdens bouw.
- **Geen legal review-traject** voor de "Managed" tier optie B — moet sowieso met een NL/EU advocaat als we die kant op gaan.

---

## 10. Eerste actie — wat doen we deze week

Niet alles tegelijk. Concreet voorstel voor de eerste 7 dagen:

1. **Fix de open bug uit sessie 39** (ffmpeg-pad in .app build). Anders gaat niets verder werken.
2. **Schrijf branding-profiel schema** (alleen het YAML/JSON schema, geen UI). 1 dag.
3. **Maak Meta Business Manager + start business verification.** Eenmalig, kan parallel lopen. 30 minuten + wachten.
4. **Maak TikTok Developer account.** Eenmalig. 30 minuten.
5. **Eén echte 30-min DJ-set uitkiezen** waarmee we de hele auto-draft flow gaan testen.
6. **Lees dit plan opnieuw en zet open vragen op een rij.**

Daarna kunnen we sessie-voor-sessie de Maand 1 items in roadmap aanpakken.

---

*Einde plan. Vragen, kritiek, wijzigingen → discussie in volgende sessie. Niet stilletjes in dit document werken — wijzigingen komen via een changelog onderaan zodat we begrijpen waarom iets is aangepast.*

## Changelog

- 2026-05-26 — v1.0 — Initiële versie na sessie post-compactie. Plan voor features 5/7/8/9 + ad-spend laag.
