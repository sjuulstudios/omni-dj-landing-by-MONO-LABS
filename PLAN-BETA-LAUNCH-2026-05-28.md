# Omni DJ — Beta Launch Master Plan

> **Sessie 60 (2026-05-28).** Master plan voor het zo snel mogelijk delen van Omni DJ met beta-testers. Geen nieuwe features tijdens dit traject.
>
> **Drie parallelle sub-plannen** die hieronder ge-referenced worden:
> 1. `PLAN-DNS-TRANSIP-CLOUDFLARE-2026-05-28.md` — DNS + landingspagina hosting
> 2. `PLAN-APPLE-DEVELOPER-2026-05-28.md` — Developer account, codesign, notarize, signed DMG
> 3. `PLAN-REBRAND-OMNI-DJ-2026-05-27.md` — bestaand rebrand-plan (Clip Live → Omni DJ)

---

## 1. Doel + scope

**Doel.** Eerste 5 tot 10 beta-testers laten downloaden, installeren, en daadwerkelijk drops detecteren + clips exporteren met de Omni DJ `.app`. Inclusief signed + notarized bundle (geen Gatekeeper-popup), live landingspagina op omnidj.com, werkende auth + reset-password flow, en een feedback-kanaal.

**Buiten scope.**
- Auto-mode backend (Fase D/E/F uit sessie 57)
- Postiz Social-publishing-laag
- Multi-tenant Supabase
- Ads-systeem
- App Store / TestFlight (voor v2, voor nu alleen DMG)
- Stripe live mode (test-mode is goed genoeg voor beta)
- 14 feature-cleanup items van sessie 59 die geen quick-win zijn

**Tijdslijn.** 2 tot 3 weken actief werk, plus 24 tot 48u Apple Developer review-wachttijd parallel.

---

## 2. Status check vooraf

Voordat je begint moet onderstaande sluitend zijn. Werk dit eerst af:

| Item | Status | Actie |
|---|---|---|
| Auth-incident sessie 59 antwoord | OPEN | Sjuul moet bevestigen of de 7 Library-projecten allemaal van `business@sjuulstudios.com` zijn. Zie `AUTH-INCIDENT-2026-05-28.md`. |
| Selection-tray sessie 59 visueel getest | OPEN | Dev-server starten, v2-flag aan, 2-3 clips selecteren in Library, top-balk checken. |
| Sessie 57+58+59 gecommit | OPEN | `git status` in `/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/Omni DJ` checken. |
| 14 feature-cleanup items go/no-go | OPEN | Per item in `PLAN-2026-05-28-FEATURE-CLEANUP.md` OK of skip. Quick-wins voor beta in scope, grote items uit. |
| TransIP login werkt | TODO | Wachtwoord paraat. |
| omnidj.com staat op je TransIP-account, niks gekoppeld | BEVESTIGD | Schone start. |

Pas door als bovenstaande dicht zijn.

---

## 3. Volgorde + parallelle tracks

Drie tracks die deels parallel kunnen. Track A is kritiek pad, B en C lopen er parallel naast.

```
Week 1
 Track A  Code rebrand sessie ──> Stable bundle ──> Signed bundle
                                                    │
 Track B  Apple Dev aanvragen ─> wachttijd ────────> Codesign cert ready
                                                    │
 Track C  TransIP nameservers ─> Cloudflare DNS ──> Landingspagina live

Week 2
 Track A  DMG hosten op landingspagina
 Track B  Reset-password + custom SMTP + email deliverability
 Track C  Privacy/ToS + feedback-kanaal

Week 3
 Smoke test door 2-3 vrienden op externe machines
 Beta-invite eerste 5-10 testers
```

Stappen hieronder zijn genummerd in volgorde van uitvoering. Tussen haakjes welke track ze horen.

---

## 4. Stap 1 — Sessie 60a: Status sluiten + commit + clean bundle (Track A, 2-3u)

**Doel.** Open punten van sessie 59 dichttrekken, alle code committen, één werkende test-bundle bouwen om aan vrienden te tonen voordat je gaat rebranden.

1. **Sjuul antwoordt auth-vraag.** Check `AUTH-INCIDENT-2026-05-28.md` einde.
2. **Sjuul test selection-tray visueel.** Start dev-server, v2 aan, selecteer clips, check top-balk.
3. **Sjuul gaat door 14 items in `PLAN-2026-05-28-FEATURE-CLEANUP.md`.** Per item: in scope voor beta (quick-win) of skip naar later.
4. **Quick-wins implementeren.** Claude doet dit code-side in een aparte sessie. Geschat: 1-2u.
5. **Git commit.**
   ```
   cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/Omni DJ"
   git status
   git add -A
   git commit -m "sessie 57-58-59 + quick-wins voor beta"
   ```
6. **Test-bundle bouwen** (nog onder naam Clip Live, alleen voor interne smoke-test):
   ```
   cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/Omni DJ"
   source venv/bin/activate
   mv "/Applications/Clip Live.app" "/Applications/Clip Live.PRE-SESSIE60.app"
   ./build_macos.sh dmg
   mv "dist/Clip Live.app" "/Applications/"
   open "/Applications/Clip Live.app"
   ```
7. **Smoke-test in bundle.** Upload set, drops detecteren, clip exporteren met captions toggle aan, MP4 controleren op caption-tekst. Auth login werkt. Reset-password werkt.
8. **Als alles groen:** door naar Stap 2 (rebrand).
9. **Als bug:** fix eerst, terug naar punt 5.

**Output.** Werkende `/Applications/Clip Live.app` met sessie 57-59 in. Niet gedeeld met externen.

---

## 5. Stap 2 — Sessie 60b: Code-rebrand naar Omni DJ (Track A, 4-6u)

**Doel.** Alle interne strings, env-vars, Bundle ID, paden, UI-copy van Clip Live naar Omni DJ. Eenmalige sessie, big-bang.

**Voorbereiding.** Beantwoord de 8 OPEN VRAGEN in sectie 14 van `PLAN-REBRAND-OMNI-DJ-2026-05-27.md`:

1. Registrar van omnidj.com — TransIP (bekend).
2. GitHub org `monolabs` bestaat of nieuw aanmaken — beslissen.
3. Apple Developer account migratie — nieuwe registratie onder MONO LABS (zie Track B).
4. Stripe-entity juridische naam — MONO LABS check.
5. `.env`-secrets roteren tijdens rebrand — aanrader: ja, gelijk meenemen.
6. Workspace-folder rename via Finder of git — Finder is al gedaan (sessie 59).
7. Status oude `clipdrop-landing-deploy/`-folder — verwijderen of archiveren.
8. Visual-identity placeholder vs nieuwe assets — placeholder OK voor beta, polish later.

**Uitvoering.** Volg `PLAN-REBRAND-OMNI-DJ-2026-05-27.md` secties 7 (sed-commando's) en 13 (big-bang volgorde). Eindigt met:

- Bundle ID `com.monolabs.omnidj`
- `CFBundleName=Omni DJ`
- `~/Library/Application Support/Omni DJ/`
- localStorage `omnidj.*` prefix
- `auth.py` blacklist updated
- Supabase project hernoemd naar Omni DJ in dashboard
- Stripe product display-names updated

**Output.** Bundle heet nu Omni DJ. Bundle ID is nieuw. NIET getekend nog (komt in Stap 6).

---

## 6. Stap 3 — Sessie 60c: App-icoon (Track A, 1-2u)

**Doel.** Custom Omni DJ app-icoon in `.icns` formaat, gekoppeld in spec-file.

**Tools.** Sjuul kan zelf in Figma of ik kan via `/canvas-design` of Figma MCP een eerste concept maken.

**Stappen.**
1. Concept maken: 1024×1024 PNG. Suggestie: zwarte cirkel of vierkant met oranje accent (waveform-shape of `OD`-monogram).
2. macOS verlangt 10 grootten in een `.iconset` folder. Script:
   ```
   mkdir omnidj.iconset
   sips -z 16 16     icon-1024.png --out omnidj.iconset/icon_16x16.png
   sips -z 32 32     icon-1024.png --out omnidj.iconset/icon_16x16@2x.png
   sips -z 32 32     icon-1024.png --out omnidj.iconset/icon_32x32.png
   sips -z 64 64     icon-1024.png --out omnidj.iconset/icon_32x32@2x.png
   sips -z 128 128   icon-1024.png --out omnidj.iconset/icon_128x128.png
   sips -z 256 256   icon-1024.png --out omnidj.iconset/icon_128x128@2x.png
   sips -z 256 256   icon-1024.png --out omnidj.iconset/icon_256x256.png
   sips -z 512 512   icon-1024.png --out omnidj.iconset/icon_256x256@2x.png
   sips -z 512 512   icon-1024.png --out omnidj.iconset/icon_512x512.png
   cp                icon-1024.png omnidj.iconset/icon_512x512@2x.png
   iconutil -c icns omnidj.iconset
   ```
3. Plaats `omnidj.icns` in `Omni DJ/dj-clip-cutter/build_resources/` (of waar de huidige icon staat).
4. In `OmniDJ.spec` (na rebrand) zet `icon='build_resources/omnidj.icns'` in de BUNDLE.
5. Rebuild en check icoon in Dock + Finder.

**Output.** `.app` toont nieuw icoon overal in macOS.

---

## 7. Stap 4 — Sessie 60d: Apple Developer (Track B, parallel)

Zie `PLAN-APPLE-DEVELOPER-2026-05-28.md` voor de volledige flow. Sjuul opent dat plan apart en volgt het.

**Kritieke milestones om deze track in sync te houden:**
- Aanmelding indienen: dag 1
- Apple review: 24-48u
- Certificaten in Keychain: dag 2-3
- `build_macos.sh` aangepast voor codesign + notarize: dag 3
- Eerste notarized DMG: dag 3-4

**Blocker.** Pas in Stap 8 (signed DMG bouwen) heb je dit nodig. Maar de wachttijd is lang, dus dag 1 starten.

---

## 8. Stap 5 — Sessie 60e: TransIP → Cloudflare DNS (Track C, parallel)

Zie `PLAN-DNS-TRANSIP-CLOUDFLARE-2026-05-28.md`. Inclusief:
- Cloudflare account + omnidj.com toevoegen
- Nameservers wisselen bij TransIP
- DNS-records configureren
- Cloudflare Pages-project aanmaken voor landingspagina
- Email-routing naar `monohq-labs.com` (waar je echte mailbox zit)
- SPF/DKIM/DMARC voor email-deliverability

**Tijdslijn.** Nameserver-propagatie 1-24u. DNS-records direct.

**Blocker.** Stap 6 (Supabase) en Stap 8 (DMG hosten) zijn afhankelijk van werkende DNS.

---

## 9. Stap 6 — Sessie 60f: Supabase productie URLs + custom SMTP (Track A, 1u)

**Voorwaarde.** DNS staat live + email-routing werkt + Apple Dev cert nog niet nodig.

**Stappen.**
1. **Supabase dashboard → Authentication → URL Configuration.**
   - Site URL: `https://omnidj.com`
   - Redirect URLs: `https://omnidj.com/*`, `https://app.omnidj.com/*`, `http://127.0.0.1:5555/*` (dev)
2. **Email Templates aanpassen.**
   - Subject + body: vervang "Clip Live" door "Omni DJ"
   - Footer logo + signature: `omnidj@monohq-labs.com`
   - Reset-password link gaat naar `https://omnidj.com/reset-password` (host op landingspagina als statisch route, of redirect naar `http://127.0.0.1:5555` voor desktop-app)
3. **Custom SMTP** (in plaats van Supabase default smtp).
   - Provider: Google Workspace (`monohq-labs.com`) of Resend (gratis 100/dag, eenvoudiger).
   - **Resend aanrader voor snelheid:** account aanmaken, API-key, in Supabase dashboard onder SMTP Settings: host `smtp.resend.com`, port 465, user `resend`, pass `<api-key>`, sender `omnidj@monohq-labs.com`.
4. **Test.** Trigger een reset-password vanuit dev-server, mail moet binnen 30s in je inbox staan.

**Output.** Reset-password en confirm-email werken met Omni DJ-branding via `omnidj@monohq-labs.com`.

---

## 10. Stap 7 — Sessie 60g: Landingspagina-content invullen + uploaden (Track C, 1-2u)

**Voorwaarde.** DNS staat live. Landingspagina v1 is gebouwd door Claude (`landing/index.html` etc, zie sectie 12 hieronder).

**Stappen.**
1. **Demo-video opnemen** (1-2 min screen recording).
   - QuickTime "New Screen Recording" of CleanShot.
   - Toon: drag-en-drop set, drops worden gemarkeerd, klik clip, export met captions.
   - Compress naar 5-10MB WebM via:
     ```
     ffmpeg -i demo.mov -vf "scale=1280:-2" -c:v libvpx-vp9 -b:v 1.5M -an demo.webm
     ```
   - Plaats in `landing/assets/demo.webm`.
2. **Screenshots maken** van 3-4 cruciale views (Analyse, Library, editor).
   - PNG 2x retina, plaats in `landing/assets/`.
3. **Email-capture endpoint.** Twee opties:
   - A. Resend + Supabase-table `waitlist` met service-role op een edge function. Meer werk maar in je stack.
   - B. Externe service: ConvertKit, Mailchimp embed, of Formspree. 10 min werk.
   - **Aanrader voor beta:** Formspree (`<form action="https://formspree.io/f/xxx">`) of een simpele Cloudflare Worker die in Supabase schrijft.
4. **DMG-link.** Direct na Stap 8 wordt deze ingevuld. Voor nu placeholder `#download`.
5. **Privacy + ToS pagina's.** Twee simpele markdown-naar-HTML pagina's (`/privacy`, `/terms`). Inhoud in Stap 9 plaatsen.
6. **Deploy.**
   - Via Cloudflare Pages (zie DNS-plan): `landing/` folder upload of git-connect.
   - Of via `wrangler` CLI.

**Output.** `https://omnidj.com` live met landingspagina, screenshots, demo-video, email-capture, placeholders voor DMG-link.

---

## 11. Stap 8 — Sessie 60h: Signed + notarized DMG bouwen + hosten (Track A+B, 1-2u)

**Voorwaarde.** Apple Dev cert in Keychain (Stap 4 voltooid), code-rebrand klaar (Stap 2), icoon in spec (Stap 3).

**Stappen.**
1. **`build_macos.sh` aangepast voor codesign + notarize** — zie `PLAN-APPLE-DEVELOPER-2026-05-28.md` sectie 6.
2. **Build:**
   ```
   cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/Omni DJ"
   source venv/bin/activate
   ./build_macos.sh dmg signed
   ```
3. **Wacht op notarize-resultaat** (5-30 min). Krijg je per email of via `xcrun notarytool log`.
4. **Staple ticket op DMG:**
   ```
   xcrun stapler staple "dist/Omni DJ.dmg"
   ```
5. **Verifieer:**
   ```
   spctl -a -t open --context context:primary-signature -vv "dist/Omni DJ.dmg"
   ```
   Output moet zijn: `accepted` + `source=Notarized Developer ID`.
6. **Upload DMG naar Cloudflare R2** (of Pages assets):
   ```
   wrangler r2 object put omnidj-downloads/Omni-DJ-1.0.0.dmg --file "dist/Omni DJ.dmg"
   ```
   Of upload via Cloudflare dashboard. Maak public link `https://downloads.omnidj.com/Omni-DJ-1.0.0.dmg` (CNAME in DNS-plan).
7. **Vervang `#download` in landingspagina** met die URL. Re-deploy `landing/`.

**Output.** Beta-tester klikt "Download" op landingspagina, krijgt signed DMG, opent zonder Gatekeeper-popup.

---

## 12. Stap 9 — Sessie 60i: Privacy, ToS, feedback-kanaal (Track C, 1-2u)

**Doel.** Juridische minimum voor data-verwerking + manier voor beta-testers om feedback te geven.

**Stappen.**
1. **Privacy Policy.** Eén pagina. Minimum-inhoud:
   - Welke data verzamel je (email + auth + DJ-set uploads + clips)
   - Waar staat het (Supabase EU + lokale machine van user)
   - Hoe lang bewaar je het
   - Wie heeft toegang
   - GDPR-rechten (inzage, verwijderen, export)
   - Contact `omnidj@monohq-labs.com`
   - Template generator: termly.io of iubenda (gratis tier).
2. **Terms of Service.** Eén pagina:
   - Beta-status disclaimer ("software is in beta, geen garantie")
   - Acceptable use (geen copyright-content uploaden voor commercieel hergebruik)
   - Account-termination clause
   - Aansprakelijkheidsbeperking
   - NL law of EU
3. **Feedback-kanaal.**
   - Simpel: maak een Discord-server "Omni DJ Beta" met 3 channels (#feedback, #bugs, #showcase). Invite-link in app + landing.
   - Of een Notion-form embedded in landingspagina /feedback.
   - **Aanrader:** Discord. Lage drempel, real-time, makkelijk te delen.
4. **In-app feedback-knop** (10 min werk).
   - In v2 sidebar footer een knop "Beta feedback" die opent `mailto:omnidj@monohq-labs.com?subject=Omni DJ feedback&body=Versie 1.0.0`.
   - Of een link naar de Discord.

**Output.** `https://omnidj.com/privacy`, `https://omnidj.com/terms` live. Discord-server live. In-app knop.

---

## 13. Stap 10 — Sessie 60j: Smoke-test door 2-3 vrienden (Track A, 2-5 dagen)

**Doel.** Externe-machine validatie voordat je naar 10 beta-testers gaat.

**Stappen.**
1. Stuur DMG-link + Discord-invite naar 2-3 vrienden (verschillende Mac-modellen, Intel + Apple Silicon).
2. Vraag ze:
   - Open Gatekeeper-check: krijgen ze waarschuwing? (Should be no als notarize werkt.)
   - Account aanmaken werkt? Reset-password werkt?
   - Eerste set uploaden + drops detecteren + clip exporteren werkt?
   - Welke bug of UX-issue valt direct op?
3. Verzamel feedback in Discord #feedback.
4. **Blocker?** Fix vóór beta-batch. Anders door.

**Output.** Vertrouwen dat 90%+ van eerste-keer-users succesvol een clip kan exporteren.

---

## 14. Stap 11 — Sessie 60k: Beta-invite eerste 5-10 testers (Track A, 1u + lopend)

**Doel.** Daadwerkelijke beta-launch.

**Stappen.**
1. **Beta-list samenstellen.** 5-10 DJs uit je netwerk. Mix van skill-niveaus.
2. **Invite-mail schrijven.** Via `omnidj@monohq-labs.com`. Inhoud:
   - Persoonlijke intro
   - Wat is Omni DJ in 2 zinnen
   - Wat verwacht je van ze: feedback, bug-reports, gebruik
   - Download-link
   - Discord-link
   - Jouw direct contact voor blockers
3. **Sturen + tracking.** Op Notion of Airtable: wie kreeg invite, wie installeerde, wie gaf feedback.
4. **Lopende support.** Discord checken 2x per dag, snel reageren op bugs, fix-priority in `HANDOVER.md`.

**Output.** Eerste echte gebruikers.

---

## 15. Risico's + mitigatie

| Risico | Impact | Mitigatie |
|---|---|---|
| Apple Dev review duurt 2+ weken | Beta wordt vertraagd | Track B dag 1 starten. Als nodig: unsigned DMG met manual override-instructie als noodoplossing voor 2-3 vrienden in Stap 10. |
| Rebrand introduceert regressies | Werkende bundle kapot | Stap 1 levert eerst stable test-bundle. Rebrand-sessie heeft volledige rollback-procedure in `PLAN-REBRAND-OMNI-DJ-2026-05-27.md` sectie 12. |
| Caption-bake bug komt terug in nieuwe bundle | Beta-testers krijgen kapotte exports | Sessie 50/51 E2E test verplicht na elke rebuild. Documenteer in `RELEASE-CHECKLIST.md`. |
| DNS-propagatie blokkeert email-flow | Reset-password mails komen niet aan | Test email-flow eerst op een staging-subdomein of via mailtester.com. |
| Supabase RLS-leak | Beta-tester ziet andere users' data | Auth-incident sessie 59 eerst dicht. Backend route-audit voor sessie 56-57 write-routes uitvoeren. Open item uit sessie 58. |
| Feedback-flood overweldigt | Sjuul kan niet bijbenen | Beta limit tot 5-10. Vooraf duidelijk SLA naar testers ("ik reageer binnen 48u"). |

---

## 16. Out-of-scope, parking-lot

Houd deze items expliciet uit beta-scope. Niet voorstellen, niet bouwen, niet opnemen in landing-copy:

- Auto-mode backend pipeline (Fase D/E/F)
- Postiz integratie
- Multi-tenant Supabase data-laag
- Ads-systeem voor content-calendar
- Stripe live mode
- App Store / TestFlight
- Windows-versie
- Mobiele app
- Sjuul's logo + visual-identity-refresh (placeholder OK voor beta)
- 14 niet-quick-win feature-cleanup items

---

## 17. Definition of Done

Beta is live als:

- [ ] `https://omnidj.com` toont landingspagina met DMG-download
- [ ] DMG is signed + notarized (geen Gatekeeper-popup)
- [ ] App heet Omni DJ, Bundle ID `com.monolabs.omnidj`, custom icoon
- [ ] Account aanmaken + login + reset-password werkt met `omnidj@monohq-labs.com` afzender
- [ ] Caption-bake werkt E2E in productie-DMG
- [ ] Privacy + ToS live
- [ ] Discord-server live + in-app feedback-knop
- [ ] 2-3 vrienden hebben succesvol een clip geëxporteerd
- [ ] Eerste 5-10 beta-invites verstuurd

---

## 18. Bestanden + referenties

| Bestand | Doel |
|---|---|
| `PLAN-BETA-LAUNCH-2026-05-28.md` | Dit document (master plan) |
| `PLAN-DNS-TRANSIP-CLOUDFLARE-2026-05-28.md` | DNS-migratie + Cloudflare Pages setup |
| `PLAN-APPLE-DEVELOPER-2026-05-28.md` | Apple Dev account + codesign + notarize |
| `PLAN-REBRAND-OMNI-DJ-2026-05-27.md` | Code-rebrand Clip Live → Omni DJ |
| `landing/index.html` | Landingspagina v1 |
| `landing/privacy.html` | Privacy Policy (Stap 9) |
| `landing/terms.html` | Terms of Service (Stap 9) |
| `AUTH-INCIDENT-2026-05-28.md` | Open auth-vraag uit sessie 59 |
| `PLAN-2026-05-28-FEATURE-CLEANUP.md` | 14 quick-wins/items voor go/no-go |
| `HANDOVER.md` | Live status tracker, update na elke stap |

---

## 19. Volgende actie

**Sjuul nu:**
1. Beantwoord auth-vraag uit `AUTH-INCIDENT-2026-05-28.md`
2. Test selection-tray visueel in dev-server
3. Beslis per van de 14 cleanup-items in `PLAN-2026-05-28-FEATURE-CLEANUP.md`: in scope of skip
4. Open `PLAN-APPLE-DEVELOPER-2026-05-28.md` in een aparte sessie en start Track B (parallel)
5. Open `PLAN-DNS-TRANSIP-CLOUDFLARE-2026-05-28.md` en start Track C (parallel)
6. Pak vandaag of morgen Stap 1 op met Claude (sessie 60a)

**Claude in vervolg-sessies:**
- Sessie 60a: quick-wins + commit + test-bundle
- Sessie 60b: rebrand uitvoeren
- Sessie 60g: landing-content finaliseren + uploaden
- Sessie 60h: signed DMG hosten

Update `HANDOVER.md` na elke stap.
