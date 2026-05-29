# Clipdrop Live - landing page

Static site. Four pages: `index.html`, `contact.html`, `privacy.html`, `terms.html`.
Shared CSS in `styles.css`, minimal JS in `script.js`.
Geen build-step.

## Bestanden in deze folder

```
landing/
├── index.html landing
├── contact.html contact pagina
├── privacy.html privacy beleid
├── terms.html algemene voorwaarden
├── styles.css shared styles
├── script.js shared JS (cookie banner, wizard, marquee)
├── favicon.svg favicon
├── og-image.svg social preview image (1200x630)
├── robots.txt SEO crawler instructies
├── sitemap.xml SEO sitemap
├── vercel.json Vercel config (headers, redirects, caching)
└── README.md dit bestand
```

## Deploy via GitHub → Vercel (aanbevolen route)

Dit is de route die je hebt gekozen. Eenmalig opzetten, daarna deploy bij elke `git push`.

### Stap 1 - GitHub repo aanmaken

1. Ga naar https://github.com/new → log in
2. Repository name: `clipdrop-live-landing`
3. Owner: jouw GitHub-account
4. Description: `Landing page for Clipdrop Live`
5. **Private** (aanbevolen - kan altijd later public)
6. NIET aanvinken: "Add a README", "Add .gitignore", "Choose a license" (heb je al)
7. Klik **Create repository**

GitHub toont nu een setup-pagina met commando's. Negeer die - gebruik onderstaande.

### Stap 2 - Lokaal git initialiseren in landing/

Open Terminal en plak deze commando's. **Eén per keer**, kijk of er geen error verschijnt voor je de volgende plakt.

cd "/Users/sjuulsmits/Documents/Claude/Projects/Clip Live/landing"

git init

git add .

git commit -m "Initial landing page commit"

git branch -M main

Daarna verbinden met je GitHub-repo. Vervang `JOUWNAAM` met je GitHub username:

git remote add origin https://github.com/JOUWNAAM/clipdrop-live-landing.git

git push -u origin main

GitHub vraagt om in te loggen. Op macOS opent een browser-popup - log in en sta toegang toe. Daarna staat de site in je GitHub repo.

### Stap 3 - Vercel project koppelen

1. Ga naar https://vercel.com/signup en log in **met je GitHub-account** (zo herkent Vercel direct je repos)
2. Klik **Add New...** → **Project**
3. Onder "Import Git Repository" zoek je `clipdrop-live-landing` en klik **Import**
4. Framework Preset: **Other** (Vercel detecteert vanzelf dat het static is)
5. Root Directory: `.` (laat staan)
6. Build Command: leeg laten
7. Output Directory: leeg laten
8. Klik **Deploy**

Na ~30 seconden krijg je een URL zoals `clipdrop-live-landing.vercel.app`. Open die - site is live.

### Stap 4 - Custom domain `clipdroplive.com` koppelen

1. In het Vercel-project → **Settings** → **Domains**
2. Type `clipdroplive.com` → **Add**
3. Vercel toont nu een DNS-record (meestal A record `76.76.21.21` of CNAME)
4. Voeg óók `www.clipdroplive.com` toe (Vercel laat dit automatisch redirecten naar root)
5. Ga naar TransIP → **Domeinnaam** → klik `clipdroplive.com` → tab **DNS-instellingen**
6. Verwijder bestaande A-records voor `@` en voeg nieuwe toe volgens Vercel's instructies
7. Wacht 10–60 min voor DNS-propagatie. Vercel checkt automatisch en geeft groen vinkje
8. SSL wordt automatisch aangezet door Vercel (Let's Encrypt)

### Stap 5 - Updates pushen

Wijzig een bestand lokaal. Daarna:

cd "/Users/sjuulsmits/Documents/Claude/Projects/Clip Live/landing"

git add .

git commit -m "Beschrijf hier wat je veranderde"

git push

Vercel ziet de push, bouwt automatisch, deployt binnen 30 seconden.

## Formspree endpoint (NOG TE DOEN)

`index.html` heeft een hero-form met `action="https://formspree.io/f/REPLACE_ME"`.
Voor activatie:
1. Ga naar https://formspree.io → maak account aan (free tier: 50 inzendingen/maand)
2. New Form → Form name `Clipdrop Live early access`
3. Kopieer de endpoint URL (bv. `https://formspree.io/f/abcd1234`)
4. In `index.html`, vervang `REPLACE_ME` met de form-ID
5. Test door zelf je email in te vullen - komt binnen op business@sjuulstudios.com

## Lokaal previewen

cd "/Users/sjuulsmits/Documents/Claude/Projects/Clip Live/landing"

python3 -m http.server 8000

Open daarna http://localhost:8000

## Alternatieve hosting (voor referentie)

### TransIP Webhosting (FTP-upload)

Werkt als je TransIP Webhosting hebt afgenomen naast de domeinnaam:
1. TransIP → Webhosting → FTP & SSH → noteer host + user + wachtwoord
2. Cyberduck (https://cyberduck.io) → File → Open Connection → FTP
3. Upload álle bestanden uit `landing/` naar de `www/` of `public_html/` folder
4. Activeer Let's Encrypt SSL via TransIP control panel

### Cloudflare Pages (drag-and-drop)

Alternatief als je weg wilt van GitHub:
1. https://dash.cloudflare.com → Workers & Pages → Create → Pages → Upload assets
2. Project name: `clipdroplive`
3. Drag de hele `landing/` folder erin → Deploy
4. Custom domains → `clipdroplive.com` → volg NS-instructies in TransIP

## Wat Vercel doet voor je

- HTTPS automatisch met Let's Encrypt
- Global CDN (~30ms latency wereldwijd)
- Auto-deploy bij elke `git push` naar `main`
- Preview-URLs voor elke feature-branch
- Gratis op het Hobby plan (genoeg voor deze landing)
- Headers + caching uit `vercel.json` worden automatisch toegepast
