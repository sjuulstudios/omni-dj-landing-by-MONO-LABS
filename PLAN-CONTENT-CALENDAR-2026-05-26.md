# Clip Live — Content Calendar + Multi-artist + Ads platform plan

> **Versie:** 1.1 — 2026-05-26
> **Auteur:** Claude + Sjuul (vervolg op PLAN-MOAT-FEATURES-2026-05-26.md)
> **Status:** Strategisch + technisch plan. Nog niet bouwen — eerst lezen, beslissen, dan fasen.
> **Scope:** Sidebar-feature Content Calendar (kanaal-overzicht, scheduling, drafts vanuit export-modal, autopublish), Multi-artist workspaces (talent manager / label / agent met N artiesten), Ads-management (Meta + TikTok + later Google).
>
> **Wijzigingen v1.1 (2026-05-26):**
> - Postiz Cloud bevestigd als publishing-route (sectie 5 + 5a uitgebreid met "wanneer wel/niet online")
> - Ads-platform verschoven naar **laatste fase** (fase 6+) — vereist meer research, met name op geld-stroom (zie sectie 7a)
> - Pricing-sectie geparkeerd als TBD — geen prijzen vastleggen tot na launch v1
> - Geld-via-platform optie expliciet uitgewerkt (PSP-vergunning, agency-of-record, Stripe Connect)

---

## 0. Waarom dit plan bestaat

Sjuul wil drie dingen tegelijk:

1. **Content Calendar** als sidebar-feature waar users hun social posts per artiest plannen en zien.
2. **Multi-artist workspaces** zodat een talent manager / label / event-organisator meerdere artiesten in één account kan beheren — of een artiest zijn account kan delen met zijn manager.
3. **Ads-management** in het platform zelf (Meta + TikTok + Google) — dezelfde ambitie als TIMA/Intellijend maar dan voor DJ-content.

Dit document beschrijft de complete architectuur, fasering, dependencies en wat er van Sjuul nodig is. Het bouwt voort op `PLAN-MOAT-FEATURES-2026-05-26.md` (feature #8 content calendar + ad-spend laag) — dit plan zoomt in op die twee blokken en voegt het **multi-tenant workspace-laag** toe die in moat-plan ontbrak.

---

## 1. Strategische logica — waarom dit een natuurlijke uitbreiding is

Clip Live's huidige user is "een DJ die clips maakt". De volgende stappen in zijn workflow zijn:
- Clips schedulen (waar/wanneer posten).
- Posts publiceren (handmatig of automatisch).
- Posts boosten met ads.
- Resultaten meten en sturen.

Door **alle stappen** in één tool aan te bieden bouw je een **echte moat**: een agent (OpusClip, Premiere AI) kan een clip knippen, maar niet jouw kalender beheren, niet jouw ad-budget verdelen, niet jouw drie artiesten als team coördineren. Het ecosysteem is de defense.

**Bijkomstig:** zodra je multi-artist hebt, opent zich een **hogere prijscategorie** (manager/label tiers €149–€699/mnd) die solo-artiest pricing nooit zou kunnen onderbouwen. Dat is waar de echte ARR zit (zie onderzoek sectie 6).

---

## 2. Huidige staat van Clip Live — feitelijk gechecked (sessie 43-staat)

| Onderdeel | Status |
|---|---|
| Flask + Supabase auth + JWT refresh | ✅ Live (sessie 28+30) |
| Supabase `profiles` met `plan/usage_this_period/stripe_*` | ✅ Live, RLS in version control (`supabase/migrations/001_rls_policies.sql`) |
| Audit log + RBAC (`user/beta/admin`) | ✅ Live (sessie 35, migraties 002+003) |
| Rate limiting (flask-limiter, 7 endpoints) | ✅ Live (sessie 32) |
| Stripe checkout + portal + webhook + edge functions | ✅ Live in **sandbox** — productie wacht op djclips.nl DNS-cutover |
| Password-reset flow end-to-end | ✅ Live (sessie 40) |
| `.app` build + DATA_DIR fix | ✅ Live (sessie 40) |
| Brand Stack (logo, fonts, watermark, colors) | ✅ Live (sessie 31+41+42) |
| Export-pipeline captions auto-bake | 🔴 In progress (sessie 43a blocker) |
| Content calendar | ❌ Bestaat niet |
| Multi-artist workspaces | ❌ Bestaat niet — alle data hangt aan `user_id` op `profiles` |
| Social publishing | ❌ Bestaat niet |
| Ads-management | ❌ Bestaat niet |

**Belangrijke beperkingen om mee te ontwerpen:**

- `profiles` is **1-op-1 met `auth.users`** — er is geen `workspace`-laag. Multi-artist vereist een **schema-uitbreiding** met `workspaces` + `workspace_members` + alle resource-tabellen krijgen `workspace_id` als scope-key.
- Stripe staat op sandbox. **Vóór** we nieuwe products/tiers in productie zetten moet eerst djclips.nl + Stripe live-mode klaar zijn (fase 3+4 op de bestaande roadmap).
- Sessie 43 (export-pipeline) **moet eerst af** — anders kunnen users geen captions in exports en is de hele calendar-pitch een halve waarheid.

---

## 3. Productvisie — wat een user concreet ziet

### Persona A — solo artiest

- Logt in, één workspace ("DJ Sjuul"), één set social-accounts.
- Maakt clip → klikt in export-modal **"Plan in Calendar"** → kiest datum/tijd + platform(s) → draft staat klaar.
- Gaat naar sidebar **Calendar** → ziet de week-/maandweergave → kan slepen, editen, verwijderen.
- Optioneel: koppelt Meta/TikTok-account → kan autopublish aanzetten met cap (max 3/dag/platform).
- Geeft eigen ad-budget op → engine maakt automatisch ad-varianten van eigen clips.

### Persona B — talent manager / label

- Logt in op één account ("MONO Management").
- Workspace-switcher linksboven (zoals Slack/Notion): kan tussen 5 DJ-workspaces wisselen.
- Per workspace: eigen social-accounts, eigen brand kit, eigen calendar, eigen ads-account.
- Kan team-members toevoegen aan een workspace (de DJ zelf, een social-media-collega) met rol (owner / editor / viewer).
- Eén Billing pagina (manager betaalt de manager-tier waar N workspaces in zitten).

### Persona C — artiest die login deelt met manager

- Eenvoudigste scenario: artiest geeft Supabase-login aan manager. Werkt direct, **zonder dat we iets bouwen**, want één login = één workspace. **Risico**: alles staat op 1 set credentials. We bieden dit aan als "single-seat sharing" maar pushen Persona B als premium-feature (manager krijgt eigen login + audit-trail wie wat deed).

---

## 4. Architectuur — vier nieuwe lagen

```
┌─────────────────────────────────────────────────────────────────┐
│  Frontend (static/index.html — Flask serves)                     │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────────┐│
│  │ Workspace   │  │  Calendar    │  │  Ads Dashboard           ││
│  │ switcher    │  │  view + post │  │  (campaigns, budget,     ││
│  │ + members   │  │  scheduler   │  │   spend, ROI)            ││
│  └─────────────┘  └──────────────┘  └──────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                            ↓ REST
┌─────────────────────────────────────────────────────────────────┐
│  app.py (Flask) — bestaand, krijgt nieuwe blueprints             │
│  • /api/workspaces/...  • /api/calendar/...                      │
│  • /api/social/...      • /api/ads/...                           │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌────────────────────┬────────────────────┬───────────────────────┐
│   Supabase (PG)    │  Postiz Cloud      │  Ad-orchestrator      │
│   nieuwe tables:   │  (publishing layer)│  (eigen Node service  │
│   workspaces       │  • OAuth per       │   op Render/VPS)      │
│   workspace_members│    artiest         │  • polling Meta API   │
│   social_accounts  │  • drafts/schedule │  • optimalisatie-loop │
│   scheduled_posts  │  • autopublish     │  • Spotify-meting     │
│   ad_campaigns     │                    │                       │
│   ad_creatives     │                    │                       │
│   ad_results       │                    │                       │
└────────────────────┴────────────────────┴───────────────────────┘
```

### Laag 1 — Multi-tenant workspaces (Supabase schema)

Nieuw schema (migratie 004):

```sql
-- 1. workspaces — één per artiest of artist-roster-item
create table public.workspaces (
  id              uuid primary key default gen_random_uuid(),
  name            text not null,                  -- "DJ Sjuul" / "Lisa Korver"
  slug            text unique,                    -- url-safe
  owner_id        uuid not null references auth.users(id) on delete cascade,
  artist_name     text,                           -- displayed branding-name
  avatar_url      text,
  brand_kit       jsonb,                          -- huidige Brand Stack komt hier
  created_at      timestamptz default now()
);

-- 2. workspace_members — wie mag in deze workspace
create table public.workspace_members (
  workspace_id    uuid references public.workspaces(id) on delete cascade,
  user_id         uuid references auth.users(id) on delete cascade,
  role            text check (role in ('owner','editor','viewer')) default 'editor',
  invited_at      timestamptz default now(),
  primary key (workspace_id, user_id)
);

-- 3. Bestaande jobs/clips/history krijgen workspace_id
alter table public.jobs add column workspace_id uuid references public.workspaces(id);
alter table public.brand_kits add column workspace_id uuid references public.workspaces(id);
-- (idem voor andere resource-tabellen die nu user-scoped zijn)
```

**RLS-patroon (migratie 005):**

```sql
-- alle workspace-scoped queries moeten checken: is current user member?
create policy "Members can read workspace" on public.workspaces
  for select using (
    id in (select workspace_id from public.workspace_members where user_id = auth.uid())
  );
```

**Billing-implicatie:** `profiles.plan` blijft op user-niveau (manager heeft één plan), maar `profiles.max_workspaces` of `profiles.plan_includes_workspaces` bepaalt hoeveel workspaces hij mag aanmaken.

### Laag 2 — Content Calendar (datamodel + UI)

```sql
create table public.scheduled_posts (
  id                uuid primary key default gen_random_uuid(),
  workspace_id      uuid not null references public.workspaces(id) on delete cascade,
  clip_id           text,                           -- verwijst naar job-output in DATA_DIR
  caption           text,
  platforms         text[] not null,                -- ['tiktok','instagram','youtube']
  scheduled_for     timestamptz not null,
  status            text default 'draft',           -- draft|scheduled|published|failed
  postiz_post_ids   jsonb,                          -- {tiktok: "abc", instagram: "xyz"}
  autopublish       boolean default false,
  created_by        uuid references auth.users(id),
  created_at        timestamptz default now(),
  updated_at        timestamptz default now()
);

create index on public.scheduled_posts (workspace_id, scheduled_for);
```

**UI in `static/index.html`:**

- Nieuwe sidebar-item "Calendar" (icon: kalender).
- Default-view: **Month**, met klikbare dagen.
- **Day-view:** lijst van geplande posts met thumbnail + caption + tijd + platform-icons.
- **Drag-to-reschedule** (klein, maar wow-factor).
- **Bulk-actie**: "duplicate this week to next".

**Vanuit Export-modal "Plan in Calendar"-button** (in sessie 43b modal-redesign een nieuwe knop naast "Save"):
- Opent inline date/time picker + platform-selector + caption-veld (pre-filled met clip-naam).
- Submit → POST naar `/api/calendar/schedule` → entry in `scheduled_posts` + draft in Postiz.

### Laag 3 — Social Publishing via Postiz

**Aanbevelingsroute uit research:** Postiz Cloud + OAuth2 Developer App. Per artiest één Postiz-organisatie. Wij praten met Postiz Public API.

```python
# pseudo — nieuwe blueprint /api/social/
@bp.route('/connect', methods=['POST'])
def connect_account():
    workspace_id = req['workspace_id']
    platform = req['platform']  # 'tiktok' | 'instagram' | 'youtube'
    # redirect user naar Postiz OAuth flow met state = workspace_id
    return redirect(postiz_oauth_url(state=workspace_id))

@bp.route('/oauth/callback')
def oauth_callback():
    code = req.args['code']
    workspace_id = req.args['state']
    pos_token = exchange_code_for_token(code)  # → pos_xxxxx
    # opslaan in social_accounts tabel, gekoppeld aan workspace
    save_social_account(workspace_id, platform, pos_token)
```

```sql
create table public.social_accounts (
  id                uuid primary key default gen_random_uuid(),
  workspace_id      uuid references public.workspaces(id) on delete cascade,
  platform          text,                           -- tiktok|instagram|youtube|x|...
  postiz_org_id     text,                           -- Postiz org id voor deze artiest
  postiz_token      text,                           -- encrypted pos_xxxxx
  handle            text,                           -- @sjuulstudios
  connected_at      timestamptz default now(),
  status            text default 'active'
);
```

**Bij scheduling:**
1. Front-end POST `/api/calendar/schedule` met clip + tijd + platforms.
2. Backend uploadt MP4 naar Postiz `/upload` endpoint (geeft URL terug).
3. Backend POST naar Postiz `/posts` met `type: "schedule"` + URL + caption + tijd.
4. Postiz post-id wordt opgeslagen in `scheduled_posts.postiz_post_ids`.
5. Op gewenste tijd publisht Postiz automatisch.

**Belangrijke trade-offs (uit research):**
- Postiz Public API rate limit = 90/uur. Bij grote rosters batchen we uploads + cap'en clip-count per uur.
- Multi-tenant token injection is open issue in Postiz (#975). **Workaround**: 1 Postiz-org per workspace — werkt prima maar betekent dat **elke artiest één keer door Postiz OAuth-scherm moet** bij eerste setup. Niet 100% headless.
- Postiz licentie = AGPL-3.0. Voor self-host + branding = Enterprise-licentie aanvragen. **Voor v1 Cloud gebruiken** = geen licentie-issue, we zijn gewoon API-consumer.

### Laag 4 — Ads-management (Meta + TikTok eerst, Google later)

**Architectuur volgt het Intellijend-model uit moat-plan (sectie 5).** Wat dit document toevoegt: concrete API-routes en de "Ad Orchestrator" als aparte Node-service.

```
[Clip Live Flask]
    ↓ POST /api/ads/campaign
[Supabase: ad_campaigns insert]
    ↓ message
[Ad Orchestrator (Node, op Render)]
    ↓ Meta/TikTok API calls
[Meta/TikTok Ads Manager]
    ↓ stats (hourly poll)
[Supabase: ad_results]
    ↓
[Clip Live Dashboard]
```

**Datamodel:**

```sql
create table public.ad_campaigns (
  id                uuid primary key default gen_random_uuid(),
  workspace_id      uuid references public.workspaces(id),
  platform          text,                           -- meta|tiktok|google
  external_id       text,                           -- Meta/TikTok campaign id
  objective         text,                           -- followers|streams|tickets|leads
  daily_budget_cents int,
  status            text,                           -- learning|active|paused|done
  optimization_rule jsonb,                          -- CTR/CPR thresholds
  spotify_artist_id text,                           -- voor stream-measurement
  created_at        timestamptz default now()
);

create table public.ad_creatives (
  id                uuid primary key default gen_random_uuid(),
  campaign_id       uuid references public.ad_campaigns(id) on delete cascade,
  clip_id           text,                           -- bron-clip uit Clip Live
  variant_label     text,                           -- "9:16 short" / "1:1 long"
  external_creative_id text,                        -- Meta/TikTok creative id
  status            text                            -- testing|winner|paused
);

create table public.ad_results (
  id                uuid primary key default gen_random_uuid(),
  creative_id       uuid references public.ad_creatives(id) on delete cascade,
  observed_at       timestamptz,
  impressions       int,
  clicks            int,
  spend_cents       int,
  cost_per_result_cents int,
  ctr_pct           numeric(5,2)
);
```

**Optimalisatie-loop** = exact zoals in moat-plan §5 beschreven (heuristieken op CTR/CPR, kill onderste 50% na 48u, schaal top 2 na 7d).

**Geld-flow:** user betaalt **direct Meta/TikTok** via zijn eigen ad-account creditcard. **Wij raken het geld niet aan.** Dit is bewust — anders worden we PSP/reseller en dat is een ander juridisch beest (zie moat-plan §5 "pricing-model"). Wij verdienen alleen aan SaaS-fee (tier "Pro + Ads" of "Manager + Ads").

---

## 5. Postiz-integratie — concreet (uit research)

| Aspect | Beslissing |
|---|---|
| Hosting | **Postiz Cloud** voor v1 (geen self-host, geen App Review nodig — Postiz heeft die al gedaan voor TikTok/IG/YT) |
| API | Public API + OAuth2 Developer App |
| Multi-tenant | 1 Postiz-org per Clip Live workspace |
| OAuth flow | User klikt "Connect TikTok" in onze UI → wij redirecten naar Postiz OAuth → user logt in op Postiz (eenmalig per artiest) → krijgt `pos_xxxxx` token terug → wij slaan op in `social_accounts` |
| Posts plannen | POST naar Postiz `/posts` met `type: "schedule"` |
| Autopublish | Werkt automatisch — wij plannen, Postiz publisht op tijd |
| Rate limit | 90/u cloud — bij grote queues batchen we |
| Licentie | AGPL onaangerakend, wij zijn API-consumer = veilig |
| Kosten | Postiz Cloud ~$23–79/mnd per Postiz-account. **Belangrijk**: dat is een kostenpost voor ons, niet voor de eindgebruiker. Wij rekenen het door in onze prijs. |

**Migratie-pad self-host later:** als we 1000+ artiesten hebben en Postiz Cloud €X/mnd × 1000 ≠ rendabel, switchen we naar self-host + Enterprise-licentie + eigen App Review. **Niet in v1 doen** — te veel werk + reviews.

**Alternatief overwogen, verworpen:** eigen Meta/TikTok/YT App Review doen. Onderzoek toont 2–6 weken doorlooptijd per platform + frequente rejections. Postiz heeft dit al, voor ons = months ahead.

### 5a. Wanneer is Clip Live online vs. lokaal — bevestigd

Sjuul vroeg: "Wordt de Postiz API enkel gebruikt wanneer de user hiervoor prompt?" — **bevestigd, ja.** Concreet wat lokaal blijft vs. wat online gaat:

**Blijft 100% lokaal (geen Postiz, geen Clip Live cloud-call):**
- Audio-analyse via librosa
- Drop-detectie + clip-generatie via ffmpeg
- Brand Stack editen (logo, fonts, kleuren, watermark)
- Caption-overlays, text-layers, ratio-switching
- Manual export naar disk (rechtermuisknop "Export" → MP4 op `~/Movies`)
- Library browsing, history, settings

**Gaat online (alleen op user-actie):**

| User-actie | Wat gaat naar buiten | Naar wie |
|---|---|---|
| "Connect TikTok/Instagram/YouTube" in workspace-settings | OAuth-redirect + later access-token | Postiz Cloud |
| "Plan in Calendar" vanuit export-modal | Gerenderde MP4 + caption + thumbnail + tijdstip | Postiz Cloud (zodat zij om 19:00 kunnen publishen ook als laptop dicht is) |
| Autopublish-trigger (geplande tijd) | Publish-call van Postiz naar TikTok/IG/YT — **wij doen niks**, dat gebeurt server-side bij Postiz | Postiz → social-platform |
| Calendar-view openen | List-call naar Postiz om status (published/failed) op te halen | Postiz Cloud |

**Belangrijke implicatie:** zodra een user op "Plan in Calendar" klikt, **verlaat de MP4 zijn machine**. Voor 99% van de users (Solo + Stage + Roster) is dat prima — sociaal posten betekent toch publiek maken. Voor het **Studio-tier** (headliners met unreleased ID's) bouwen we een opt-out: "Studio-mode = manual export only, geen Postiz-koppeling toegestaan" zodat unreleased materiaal nooit op een externe server staat.

**Storage-implicatie bij Postiz Cloud:** Postiz cached de gerenderde MP4 totdat de geplande post afgegaan is, daarna wordt hij conform hun retention-policy verwijderd (te bevestigen in hun Terms voor we live gaan). Wij houden in onze eigen DB alleen een verwijzing (`postiz_post_ids`) plus de oorspronkelijke clip-file lokaal — geen dubbele cloud-storage van onze kant.

---

## 6. Doelgroepen & pricing — onderbouwd (uit research)

> **🅿️ GEPARKEERD (v1.1, 2026-05-26):** Sjuul wil pricing nog niet vastleggen — "te veel wisselen voor nu". De prijspunten + tier-structuur hieronder blijven in het plan als **referentie/voorstel** maar zijn **niet beslist**. Geen Stripe-products aanmaken, geen pricing-pagina updaten, geen marketing op deze bedragen baseren totdat Sjuul expliciet beslist. Onderzoek-data (sectie hieronder) blijft geldig.

### Doelgroepen op volgorde van betalingsbereidheid

1. **Solo artiest/DJ** — €0–25/mnd, prijsgevoelig
2. **Pro/touring DJ** — €25–100/mnd
3. **Social-media manager (freelance)** — €50–150/mnd per client-pakket
4. **Talent manager / agent** — €100–500/mnd (3–15 artiesten)
5. **Indie record label** — €200–2.000/mnd
6. **Majors/agencies** — €2k–25k/mnd enterprise

**Witte vlek (uit research):** er bestaat **vrijwel niets** specifiek voor DJ-managers. B-Side, A.MUSE, Toolroom Management gebruiken Notion + Soundcharts + Linkfire. Clip Live kan deze niche claimen.

### Voorgestelde tier-structuur (vervangt/verfijnt tier-tabel uit moat-plan §8)

| Tier | Naam | Prijs/mnd | Workspaces | Ads-engine | Doel |
|---|---|---|---|---|---|
| Free | Starter | €0 | 1 | – | Test |
| Solo | Clip | €19 | 1 | – | Hobby DJ |
| Solo Pro | Stage | €49 | 1 | – | Pro DJ |
| Solo Pro + Ads | Stage+Ads | €79 | 1 | ✅ | Pro DJ met budget |
| Manager | Roster 5 | €149 | 5 | – | Manager met 5 artiesten |
| Manager + Ads | Roster 5 + Ads | €229 | 5 | ✅ | Manager met ad-spend |
| Label | Roster 15 | €399 | 15 | ✅ | Indie label |
| Studio (privacy) | Studio | €99 | 1 | optioneel | Headliner met unreleased ID's |
| Enterprise | Custom | €1k+/mnd | onbeperkt | ✅ | Majors |

**Belangrijk:** prijzen zijn voorstel. **Sjuul moet beslissen** voor we Stripe-products aanmaken. Aanbeveling: launch met Solo + Stage + Roster-5, voeg Roster-15 toe als er aanvraag is.

**Account-sharing-policy:** Solo-tiers staan login-sharing toe ("sharing met je manager is fine, maar je krijgt geen audit-trail"). Manager-tier biedt **echt multi-user** met rollen en audit-log → upsell-argument.

---

## 7. Ads-platform — uitgesteld naar laatste fase (v1.1, 2026-05-26)

> **🚫 BESLISSING SJUUL (2026-05-26):** Het hele ads-systeem wordt **pas als allerlaatste gebouwd**. Reden: meer research nodig op geld-flow (zie sectie 7a hieronder), App Review-trajecten, en het is voor v1 niet de eerste waarde-toevoeging. We bouwen eerst multi-tenant + calendar + Postiz publishing en valideren daar de eerste users mee.
>
> **Wat dit betekent voor de roadmap:**
> - Fase 4 (Meta Ads) + Fase 5 (TikTok Ads) verschuiven naar **na** Fase 3 (Postiz publishing) **en** na een **research-fase 4a** waarin Sjuul + Claude de open vragen onder 7a beantwoorden.
> - Meta Business Verification + TikTok For Business **hoeven niet meer met urgentie** gestart te worden — pas zodra we serieus richting ads-fase gaan.
> - De informatie hieronder blijft staan voor toekomstige referentie.

### Wat er nodig blijft (referentie, niet nu uitvoeren)

Uit research blijkt: **business verification + App Review duren weken** en hangen volledig op Sjuul's actie. Deze stappen lopen parallel aan dev-werk wanneer we eraan toe zijn.

| Actie | Doorlooptijd | Wat Sjuul moet doen |
|---|---|---|
| **Meta Business Verification** | 3–14 dagen | KVK-uittreksel, DNS TXT op djclips.nl, KVK-adres, evt. bankafschrift |
| **Meta Developer App + Marketing API** | 1 dag setup + 2–6 weken review | App aanmaken, privacy policy live op djclips.nl, demo-video opnemen |
| **TikTok For Business + developer-registratie** | 3–7 dagen verify + 2–4 weken review | TikTok Business account, developer-agreement tekenen |
| **Google Ads MCC + developer token** | 4–8 weken (Standard Access) | Google Cloud project, MCC aanvragen, tool-demo voor Google rep |
| **Privacy policy uitbreiden** | 1 dag | "We manage ads on your behalf"-clausule erin (verplicht door alle drie reviews) |

**Aanbeveling (oud, v1.0):** start Meta + TikTok direct na djclips.nl DNS-cutover. **Vervangen door v1.1-beslissing**: pas opstarten na Fase 3 + research-fase 4a.

---

## 7a. Geld-flow via Clip Live — research-vraag (v1.1, 2026-05-26)

> Sjuul vroeg: "Ik wil geld WEL via onze tool laten lopen. Wij geven het uit en mix-en-matchen accounts." Dit is een **fundamentele wijziging** ten opzichte van v1.0 (waar geld direct van user naar Meta/TikTok zou stromen). Dat opent juridische en operationele complexiteit die we eerst moeten doorgronden. Daarom is de hele ads-fase **research-first** gemaakt.

### Wat "geld via ons" betekent

Drie mogelijke modellen, met oplopende complexiteit:

**Model A — Reseller / agency-of-record**
- Wij worden formeel "advertising agency" voor de user.
- User betaalt **ons** (bv. via Stripe) een totaal-budget = ad-spend + onze fee.
- Wij zetten Meta/TikTok ad-accounts op **op onze eigen Business Manager** namens de klant.
- Wij betalen Meta/TikTok met **onze creditcard**, factureren door aan user.
- **Voordeel:** wij hebben volledige controle over budget-allocatie tussen klanten (mix-en-matchen).
- **Risico:** Meta's ToS verbiedt "reselling ad-spend" zonder Meta Marketing Partner-status. Strikt genomen mag dit niet zonder partner-badge, en die status krijg je pas met track record.
- **Juridisch:** in NL = agency-of-record-constructie. Vereist heldere klant-overeenkomst, factuur-flow, BTW-behandeling van doorberekende ad-spend (kan vrijgesteld of belast zijn — fiscaal-advies nodig).

**Model B — Payment service provider (PSP)**
- User koppelt eigen Meta/TikTok-account, ad-spend gaat direct van Meta/TikTok-factuur naar user-creditcard.
- Maar user betaalt **ons** een vast bedrag dat wij **doorstorten** naar Meta/TikTok als prepaid ad-credits op zijn account.
- Wij hanteren dus geld dat niet van ons is → **PSP-vergunning vereist** of small-PI-ontheffing bij DNB.
- **PSD2/Wft-vereisten:**
  - Startkapitaal ~€20.000 (small payment institution) of €125.000 (volledige PSP).
  - DNB-aanvraag duurt 3–6 maanden, vergt jurist.
  - AML/KYC-verplichtingen op elke transactie.
  - Jaarlijkse audit door externe accountant.
  - Verplicht systeem voor klant-geld scheiding (escrow-rekening).
- **Niet aan te raden** voor v1, alleen relevant als wij echt prepaid credits willen aanbieden.

**Model C — Stripe Connect platform**
- Stripe levert de payment-licentie als platform-provider.
- User betaalt **ons platform** via Stripe Connect (Custom of Express account).
- Stripe verzorgt KYC, payouts, AML voor ons.
- Wij krijgen "platform fee" automatisch ingehouden.
- Daarna draaien wij ad-campagnes (Model A-style) met dit geld.
- **Voordeel:** geen DNB-vergunning, Stripe is hier al voor licensed.
- **Beperking:** Stripe Connect heeft strikte use-cases — "advertising agency" is acceptable maar moet duidelijk gepositioneerd worden in onboarding. Stripe kan accounts pauzeren als use-case afwijkt.
- **Status NL:** Stripe Connect werkt in NL, prijs ~0,25% extra bovenop normale Stripe-fee.

### Wat we nu nog niet weten — research-fase 4a

Voor we Fase 4 (Ads) bouwen moeten we beantwoorden:

1. **Meta's ToS** — mogen wij ad-accounts op onze BM zetten en doorfactureren aan klanten **zonder** Marketing Partner-badge? Hard onderzoek in [Meta Business ToS](https://www.facebook.com/legal/commercial_terms) en gesprekken met Meta-sales.
2. **TikTok's reseller-policy** — zelfde vraag, andere platform.
3. **Welk model past best** (A vs. B vs. C) gegeven NL-fiscaliteit + wens om "mix-en-matchen" tussen klant-accounts.
4. **Fiscaal advies** — BTW op doorgefactureerde ad-spend (verlegging? doorberekening? belast?).
5. **KvK/Wft-check** — moet ons huidige bedrijf (SjuulStudios) zich registreren als financiële dienstverlener?
6. **Verzekering** — beroepsaansprakelijkheid + ad-budget-misbruik dekking.
7. **Klant-overeenkomst-template** — wat staat erin als wij €5.000 ad-budget voor een klant beheren?

**Inschatting research-tijd:** 2–3 weken Sjuul + Claude + 1 sessie met NL-jurist en/of fiscalist (€500–€1.500 advies-kosten).

### Mix-en-matchen tussen klant-accounts — wat dat technisch betekent

Sjuul's wens: "Deze accounts kan je per artiestenprofiel inladen — als je talent managers hebt, kan je meerdere artiesten toevoegen."

Concreet: een talent manager wil voor zijn 5 artiesten één gezamenlijk maandbudget van €5.000 hebben, dat hij dynamisch verdeelt (artiest A loopt goed → €2.000, artiest B onder de maat → €500). Dat vereist:

- **Eén "ads-budget"-pool per workspace-owner** (de manager) i.p.v. per workspace.
- **Per workspace (artiest) een sub-budget** dat de manager kan herverdelen.
- **Onze orchestrator** beheert echte ad-accounts (Meta BM's) en alloceert budget volgens deze pool-structuur.
- **Dashboard** voor manager waar hij real-time kan zien wat elke artiest opmaakt en knoppen om sneller te shifren.

Dit is **alleen mogelijk in Model A of C** (waar wij het geld in handen hebben). In Model "user betaalt direct" (oude v1.0-aanname) kan dit niet — dan zit het budget vast op de account van de user en kan jij niet shiften.

**Implicatie voor schema:** als we deze richting gaan, krijgt het `ad_campaigns`-datamodel een extra laag `owner_budget_pools` met `manager_user_id` + `total_budget_cents` + `current_period_start`. Te ontwerpen tijdens Fase 4 design.

---

## 8. Fasering — concreet wat we bouwen in welke volgorde

> Realistische schatting voor één developer (Claude + Sjuul samen, ~10–15u/week). Voeg buffer toe voor reviews en bug-fixing.

### Fase 0 — Voorbereiding (parallel, kost 0 dev-tijd, alleen wachten)

- ✅ Sessie 43 (export-pipeline fix) — al ingepland, blocker voor de hele rest
- 📅 djclips.nl DNS-cutover via Cloudflare
- 📅 Stripe live-mode aan (na DNS)
- 📅 Privacy policy uitbreiden met "we manage social publishing"-clausule (ads-clausule pas later, samen met Fase 4a)
- ⏳ **Meta Business Verification + TikTok For Business** — **NIET nu starten** (verschoven naar Fase 4a research zoals beslist in v1.1)

### Fase 1 — Multi-tenant fundament (3–4 weken dev)

> **Niets van het bovenste kan worden gebouwd zonder dit. Eerst dit.**

1. **Migratie 004** — `workspaces` + `workspace_members` tabellen
2. **Migratie 005** — RLS-policies op workspaces
3. **Migratie 006** — `workspace_id` kolom toevoegen aan bestaande resource-tabellen (jobs, brand_kits, history)
4. **Data-migratie** — voor elke bestaande user automatisch 1 workspace aanmaken op basis van zijn `artist_name` of `full_name`
5. **Backend** — alle `/api/*` endpoints uitbreiden met workspace-scope; nieuwe `/api/workspaces/...` CRUD
6. **Frontend** — workspace-switcher linksboven (zoals Slack), workspace-management screen onder Settings
7. **Stripe-uitbreiding** — `profiles.max_workspaces` ophalen uit plan, blokkeren bij overschrijden

**Verificatie:** existing single-user accounts blijven werken (default workspace). Manager kan tweede workspace aanmaken als hij Roster-tier heeft.

**Backup-strategie:** branch `feature/workspaces`, alles via PR-style commits. Backup van prod-DB vóór data-migratie.

### Fase 2 — Content Calendar UI + datamodel (2–3 weken dev)

1. **Migratie 007** — `scheduled_posts` tabel + RLS
2. **Backend** — `/api/calendar/list?from=X&to=Y`, `/api/calendar/schedule`, `/api/calendar/update`, `/api/calendar/delete`
3. **Frontend** — kalender-component (eigen build met canvas, of FullCalendar lib — beslissen). Month + Week view.
4. **Integratie in export-modal** — "Plan in Calendar"-knop in sessie 43b modal-redesign
5. **Bulk-acties** — duplicate week, drag-to-reschedule

**Belangrijk:** in fase 2 staan posts in onze DB maar publishen we **nog niets**. Het is een draft-systeem totdat fase 3 live is.

### Fase 3 — Postiz publishing-laag (3–4 weken dev)

1. **Migratie 008** — `social_accounts` tabel
2. **Postiz Cloud-account aanmaken** + Developer App + OAuth2
3. **Backend** — `/api/social/connect`, `/api/social/oauth/callback`, `/api/social/disconnect`
4. **Sync-laag** — bij scheduling: upload naar Postiz + create scheduled post; bij delete: cancel in Postiz
5. **Frontend** — "Connect TikTok/IG/YT"-knoppen per workspace in Settings
6. **Autopublish-toggle** + safety-cap (max 3/dag/platform)
7. **Status-polling** — Postiz callback of polling om `scheduled_posts.status` te updaten naar `published`/`failed`

**Verificatie:** end-to-end test: clip → Plan in Calendar → schedule → 5 minuten later check Postiz published → check real TikTok feed.

### Fase 4 — Polishing + Mobile companion (was Fase 6 in v1.0)

> **Volgorde-wijziging v1.1 (2026-05-26):** in v1.0 was dit Fase 6 (na ads). In v1.1 wordt het Fase 4 omdat de ads-fase naar het einde verschuift. Dit zijn de niet-ads-features die het product afmaken voor de eerste paid users.

- Mobile push-notificatie voor approve-flow (zoals beschreven in moat-plan §4)
- Approval-flow polishing (bulk-approve, swipe-interface in web)
- Caption-generatie via Ollama (lokaal LLM) of cloud-API (per tier)
- Analytics-laag: per-clip performance (views, CTR) terug naar Calendar zonder ads
- Watch-folder + auto-draft-pipeline (moat-plan §4 fase 8)

### Fase 4a — Ads research (was Fase 0 in v1.0)

> **Pre-werk voor de ads-fasen.** Geen dev. Sjuul + Claude beantwoorden de 7 vragen uit sectie 7a. Doorlooptijd 2–3 weken + juridisch/fiscaal advies.

1. Meta + TikTok reseller-policy onderzoek
2. Model-keuze A vs. B vs. C (agency / PSP / Stripe Connect)
3. Sessie met NL-jurist + fiscalist
4. Beslissing op geld-flow + opzet juridische entiteit waar nodig
5. **Pas hierna**: Meta Business Verification + TikTok For Business starten

### Fase 5 — Meta Ads orchestrator (was Fase 4 in v1.0, nu na alles anders)

> **Vereist Fase 4a beslissingen + Meta Business Verification klaar.** Begin alleen aan dev als verification submitted is.

1. **Meta App + Marketing API** ready + business verification compleet
2. **Migratie X** — `ad_campaigns`, `ad_creatives`, `ad_results`, `owner_budget_pools` tabellen (laatste alleen als Model A/C gekozen)
3. **Ad Orchestrator service** — nieuwe Node.js repo, deploy op Render (~$7/mnd)
4. **Backend** — `/api/ads/connect-meta`, `/api/ads/create-campaign`, `/api/ads/pause`, `/api/ads/budget-pool` (Model A/C)
5. **Optimalisatie-loop** — heuristieken op CTR/CPR (zie moat-plan §5)
6. **Spotify for Artists OAuth** — voor stream-measurement
7. **Frontend dashboard** — campagne-overzicht, daily spend, top-performing creatives, ROI, mix-en-match-budget-UI voor managers

**App Review parallel** — werk aan dev terwijl Meta de review doet.

### Fase 6 — TikTok Ads (was Fase 5, 3 weken dev + review-tijd)

Zelfde structuur als fase 5, maar voor TikTok Marketing API. Kan deels vanaf bestaande orchestrator.

### Fase 7 — Google Ads + "Managed"-tier (verder uit, niet voor v1)

- Google Ads (lange App Review 4–8 wkn voor Standard Access)
- Refinement van geld-flow op basis van leerlessen Fase 5+6
- White-label voor labels (eigen branding van Clip Live binnen label-account)

---

## 9. Totale werk-schatting (v1.1 — ads verschoven naar einde)

| Fase | Dev-tijd | Wachttijd (parallel) | Sjuul-input |
|---|---|---|---|
| 0 | 0 (al ingepland) | sessie 43 + djclips.nl | sessie 43 afronden |
| 1 — Multi-tenant | 3–4 weken | — | workspace-naam beslissen |
| 2 — Calendar UI | 2–3 weken | — | UI-feedback |
| 3 — Postiz publish | 3–4 weken | — | Postiz Cloud account |
| 4 — Polish + mobile | 4+ weken | — | feedback early users |
| 4a — Ads research | 0 dev | 2–3 weken research + jurist | KVK-stukken, juridisch advies budget €500–€1.500 |
| 5 — Meta Ads | 4–6 weken | 2–6 weken review | Business verify, demo-video |
| 6 — TikTok Ads | 3 weken | 2–4 weken review | TikTok demo-video |
| 7 — Google + Managed | 4+ weken | 4–8 weken review | Google MCC aanvragen |

**Totaal Fase 1–4 (zonder ads): ~13–15 weken dev** (3–3,5 maand). Dit is de **v1**.

**Totaal Fase 1–7 (inclusief ads): ~28–35 weken dev** (7–9 maanden) + reviews parallel.

**Aanbeveling:** mik op v1 (Fase 1–4) als eerste paid launch. Ads erbij in v2 zodra geld-flow-research klaar is.

---

## 10. Wat ik concreet van Sjuul nodig heb (v1.1)

### Direct (deze week)

1. ~~Beslissing tier-naming en prijzen~~ — **GEPARKEERD** (Sjuul wil nog niet vastleggen).
2. ✅ **Postiz Cloud akkoord** (bevestigd 2026-05-26).
3. **Beslissing workspace-naam** — Workspace / Roster / Artist / Project — voor UI-copy en datamodel.

### Vóór Fase 1 (binnen 2 weken)

4. **Sessie 43 (export-pipeline) klaar** — anders heeft Calendar geen exporteerbare clips.
5. **djclips.nl live** — nodig voor Postiz OAuth-callback URL + later voor reviews.

### Vóór Fase 3 (Postiz publishing)

6. **Postiz Cloud-account aanmaken** + Developer App + API-keys.
7. **Privacy policy + Terms uitgebreid** met data-handling voor social publishing (ads-clausule pas later, niet nu).

### Vóór Fase 4a (Ads-research) — niet urgent meer

8. Bereid je voor op 2–3 weken research samen + sessie met NL-jurist/fiscalist (€500–€1.500).
9. KVK-uittreksel + domein-eigendom-bewijs op djclips.nl (wel handig om al klaar te hebben liggen).

### Optioneel maar handig

10. **Mockups van de Calendar-UI** — als je voorkeur hebt voor specifieke layout (zoals de TIMA-screenshots), deel die zodat we de design-richting kunnen vastleggen vóór we bouwen.

---

## 11. Risico's + mitigaties

| Risico | Impact | Mitigatie |
|---|---|---|
| Multi-tenant data-isolatie bug → workspace A ziet data van workspace B | Catastrofaal (zelfde categorie als sessie 28-bug) | RLS-policies in version control, test-account-matrix, security-audit voor fase 1 oplevering |
| Postiz API verandert / Postiz Cloud gaat down | Hoog (heel social-laag stopt) | Self-host migratie-pad documenteren, contingency-tijd reserveren |
| Meta App Review afgewezen | Hoog (geen Meta Ads) | Demo-video schoon, positioneer als "self-service tool for own ad-account", eerste rejection inplannen |
| TikTok-policy verandert (frequent) | Middel | API-versie pinnen, monitoring op deprecation-warnings |
| Stripe migratie sandbox → live tijdens fase 1 levert downtime | Middel | Migration-window plannen, dubbele test in sandbox, rollback-plan |
| Sjuul overbelast (sessie 43 + verificaties + dev-werk + dagjob) | Hoog | Strikte fase-volgorde houden, niet vooruitlopen, voorrang aan blocker-fixes |
| Postiz AGPL-licentie issue | Laag (we zijn API-consumer) | Niets in source aanpassen, gewoon API gebruiken. Bij self-host: Enterprise-licentie |

---

## 12. Wat dit plan bewust NIET dekt

- **Mobile companion app** — komt later, eerst pipeline werkend.
- **Multicam (feature #5 uit moat-plan)** — losse track, niet in dit plan.
- **AI-caption-generatie** — staat in moat-plan §4, kan parallel met Calendar maar is geen blocker.
- **Managed-tier met % van ad-spend** — juridisch beest (PSP-vergunning), pas fase 7.
- **Google Ads integratie** — te lange App Review (4–8 wkn Standard Access), uitstellen tot v2.
- **Witte-label voor labels** (eigen branding van Clip Live binnen label-account) — interessante v3-feature, niet nu.
- **Analytics-feedback-loop terug naar editor** (welke clip-types presteren best per genre) — staat in moat-plan §1, fase 6+.

---

## 13. Eerste actie — wat doen we deze week (v1.1)

Concreet voor week 22 (2026-05-26 tot 2026-06-01):

1. **Sjuul leest dit plan v1.1** en zet open vragen op een rij.
2. **Sjuul beslist workspace-naam** (Workspace / Roster / Artist / Project).
3. ~~Meta Business Verification~~ ~~TikTok For Business~~ — **uitgesteld** naar Fase 4a (v1.1-beslissing).
4. **Sjuul rondt sessie 43 (43a + 43b + 44) af** — export-pipeline blocker voor Calendar v1.
5. **Sjuul plant djclips.nl DNS-cutover** met Cloudflare.
6. **Wij plannen sessie 45+ in** om Fase 1 (multi-tenant fundament) te beginnen zodra 43 + djclips.nl klaar zijn.

Daarna fase-voor-fase de roadmap doorlopen: Multi-tenant → Calendar → Postiz publishing → Polish → **dan pas** ads-research starten.

**Niet eerder beginnen aan Calendar dan dat de multi-tenant fundering staat.**

---

## 14. Open vragen voor Sjuul

Geen retorische — letterlijk te beantwoorden voor we beginnen:

1. **Pricing:** ga je akkoord met voorstel in sectie 6, of wil je andere bedragen?
2. **Workspace-naam:** "Workspace", "Roster", "Artist", "Project" — wat past bij DJ-doelgroep?
3. **Account-sharing op solo-tiers:** toestaan of forceren naar Manager-tier (revenue vs. friction)?
4. **Postiz Cloud:** akkoord, of toch self-host onderzoeken?
5. **Ads pricing:** plat €30 bovenop tier (mijn voorstel), of een % van ad-spend (Managed-model later)?
6. **Spotify-koppeling:** verplicht of optioneel binnen Ads-tier?
7. **Mobile approve-flow:** v1 of v2? (mijn voorstel: v2)

---

## Changelog

- 2026-05-26 — v1.0 — Initieel plan na onderzoek (Postiz, doelgroepen, Meta/TikTok/Google API's). Bouwt voort op PLAN-MOAT-FEATURES-2026-05-26.md en respecteert sessie 43 als blocker.
- 2026-05-26 — v1.1 — Sjuul-beslissingen verwerkt:
  - Postiz Cloud bevestigd + sectie 5a toegevoegd over "wanneer wel/niet online".
  - Ads-systeem verschoven naar laatste fase (was Fase 4 → nu Fase 5+6+7). Multi-tenant + Calendar + Postiz publishing + Polish komen eerst.
  - Nieuwe Fase 4a "Ads research" toegevoegd met geld-flow-research (Model A agency / B PSP / C Stripe Connect).
  - Sectie 7a uitgewerkt: "geld via Clip Live" + PSP-vergunning-uitleg + mix-en-matchen-budget voor managers.
  - Pricing-sectie (6) geparkeerd als TBD — prijzen niet vastleggen tot na v1.
  - Meta + TikTok verificatie-acties **niet meer met urgentie** in sectie 10.
  - Werkschatting-tabel sectie 9 bijgewerkt: v1 (Fase 1–4) = 13–15 wkn, full v2 (incl. ads) = 28–35 wkn.
