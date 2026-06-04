# Omni DJ — Project Context

## Wat is dit
Python/Flask tool die drops en buildups detecteert in DJ-sets en automatisch korte vertikale/landscape videoclips genereert (30–60s). Draait lokaal op Sjuul's machine, uiteindelijk bedoeld als downloadbare .dmg/.exe app.

## Wie werkt eraan
Sjuul Smits — niet-technisch op devniveau. Altijd uitleggen wat een commando doet. Nooit meerdere stappen tegelijk geven. Terminal-instructies altijd letterlijk, zonder markdown code fences.

## App starten
```
cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/dj-clip-cutter"
./start.sh
```
Daarna browser openen op: http://127.0.0.1:5555

## Projectstructuur
```
Omni DJ/
├── .claude/CLAUDE.md          ← dit bestand
├── HANDOVER.md                ← altijd als eerste lezen
├── INSTALL.md                 ← volledige installatiegids
├── QUICK-REFERENCE.md         ← terminal cheatsheet voor Sjuul
├── omnidj.com/                ← Next.js website (LIVE op omnidj.com)
│   ├── app/                   ← pagina-routes (Next.js App Router)
│   ├── components/            ← React componenten
│   ├── public/                ← statische assets
│   ├── next.config.mjs        ← output: 'export' (statische site)
│   └── tsconfig.json          ← remotion/ uitgesloten van build
├── landing-omnidj/            ← OUDE simpele landing (niet meer actief)
└── Omni DJ/                   ← app-code (Flask + frontend)
    ├── app.py                 ← Flask entry point
    ├── analyzer.py            ← drop-detectie algoritme (librosa)
    ├── cutter.py              ← video snijden (ffmpeg)
    ├── static/index.html      ← frontend (SPA)
    ├── start.sh               ← start script (venv + flask)
    └── requirements.txt       ← Python dependencies
```

## Website (omnidj.com)
- LIVE via Cloudflare Pages (`omni-dj-landing-by-mono-labs`)
- Repo: `sjuulstudios/omni-dj-landing-by-MONO-LABS`, branch `main`
- Build: `npm run build` in `omnidj.com/`, output naar `out/`
- Auto-deploy bij push naar main
- Nog open: Formspree-endpoint (`REPLACE_ME`) + DMG-URL (`REPLACE_DMG_URL`)

## Tech stack
- **Backend:** Python 3, Flask 3.0
- **Audio analyse:** librosa, numpy, scipy, soundfile
- **Video:** ffmpeg-python
- **Optioneel (niet actief):** torch + demucs (AI source separation), Google OAuth (YouTube upload)

## Bekende problemen / niet opnieuw implementeren
- **Duplicate clips bug:** clips tonen soms identieke video in plaats van unieke drops — dit is een terugkerend probleem, check of het al gefixed is voor je iets verandert aan de clip-logica
- **Large-file pipeline:** bij grote audiobestanden loopt de pipeline soms vast — check timeouts en chunksize
- **UI:** is al redesigned naar OpusClip-stijl — niet terugdraaien naar oude layout

## Aanpak (altijd volgen)
1. Lees HANDOVER.md als die bestaat — altijd als eerste stap
2. Diagnose → aanpak voorstellen → wachten op "ja" → pas dan uitvoeren
3. Minimale impact: doe alleen wat gevraagd is
4. Meld als de scope groter is dan verwacht

## Toekomstige doelen (nog niet implementeren)
- OAuth voor TikTok/Instagram upload
- Patent aanvragen (NL/EU/global)
- Packagen als .dmg/.exe

## Veiligheid
- Nooit API keys of wachtwoorden in bestanden opslaan
- Altijd bevestiging vragen voor bestandsverwijdering
