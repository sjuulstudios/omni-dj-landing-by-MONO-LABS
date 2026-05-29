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
├── INSTALL.md                 ← volledige installatiegids
├── QUICK-REFERENCE.md         ← terminal cheatsheet voor Sjuul
├── clip-live-redesign.html    ← UI mockup (OpusClip-stijl)
└── dj-clip-cutter/
    ├── app.py                 ← Flask entry point
    ├── analyzer.py            ← drop-detectie algoritme (librosa)
    ← cutter.py                ← video snijden (ffmpeg)
    ├── uploader.py            ← toekomstige TikTok/Instagram upload
    ├── start.sh               ← start script (venv + flask)
    ├── requirements.txt       ← Python dependencies
    ├── config.json            ← app instellingen
    └── static/                ← frontend bestanden
```

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
