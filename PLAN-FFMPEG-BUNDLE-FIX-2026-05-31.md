# Plan: ffmpeg/ffprobe correct bundelen in de gesignde .app

> Sessie 66 (2026-05-31). Blocker gevonden tijdens .app smoke-test.
> Schrijfdatum: 31 mei 2026.

## Het probleem (bevestigd, niet vermoed)

Bij het testen van de gesignde `/Applications/Omni DJ.app` faalt elke video-upload met:
`Invalid video file: ffprobe failed — not a valid video file`.

Directe test van de gebundelde ffprobe gaf de echte oorzaak:
```
dyld: Library not loaded: /opt/homebrew/Cellar/ffmpeg/8.1.1/lib/libavdevice.62.dylib
Reason: ... 'libavdevice.62.dylib' not valid for use in process: ... different Team IDs
```

Wat er gebeurt:
1. `build_macos.sh` (regels 120-122) doet een kale `cp` van de Homebrew-`ffmpeg`/`ffprobe`
   naar `Contents/Resources/bin/`, MAAR kopieert hun gedeelde libraries (dylibs) niet mee.
2. Die binaries zoeken hun dylibs nog steeds op `/opt/homebrew/Cellar/ffmpeg/...`.
3. Onder de hardened runtime (vereist voor notarization) weigert macOS dylibs te laden die
   een ander Team ID hebben dan de app. Homebrew-dylibs hebben dat. → ffprobe abort meteen.

**Impact: kritiek.** Op Sjuul's Mac leek dit te werken zolang Homebrew aanwezig was, maar:
- in de gesignde .app faalt het altijd (different Team IDs);
- op een beta-tester zonder Homebrew/ffmpeg ontbreken de dylibs volledig → elke upload faalt.
Zonder fix is de .app onbruikbaar voor iedereen behalve een dev met Homebrew + unsigned build.

## Bijkomend (kleiner) probleem

De code roept ffprobe/ffmpeg deels kaal aan (`['ffprobe', ...]`, app.py regels 620/736/1428),
leunend op PATH via de launcher-wrapper. Robuuster is om expliciet naar de bundle-binary te
wijzen. Niet strikt nodig als de wrapper klopt, maar wel netter en minder fragiel.

## Twee oplossingsrichtingen

### Optie A — Static binaries bundelen (AANBEVOLEN)
Vervang de Homebrew-ffmpeg door **static** builds die geen externe dylibs nodig hebben.
Eén zelfstandig bestand per binary, niets om te herschrijven.

- Bron met gesignde + genotariseerde arm64-builds: **Martin-Riedl.de**
  (`https://ffmpeg.martin-riedl.de/`), of de npm-pakketten `ffmpeg-ffprobe-static` /
  `eugeneware/ffmpeg-static` (arm64-support).
- Build-script wijziging: download/gebruik de static binaries i.p.v. `cp $(command -v ffmpeg)`.
- Codesign-stap signt ze gewoon mee (zit al in het sign-blok voor `Resources/bin/*`).

Voordelen: simpel, robuust, werkt op elke Mac (met/zonder Homebrew), klein risico.
Nadelen: extra download-stap of vendored binaries in de repo (~80-100 MB elk); even checken
welke codecs de static build bevat (we hebben minimaal h264 + drawtext/libfreetype nodig —
zie app.py SESSIE 22-comment over drawtext).

### Optie B — Homebrew-dylibs meebundelen + herschrijven
Houd Homebrew-ffmpeg, kopieer alle afhankelijke dylibs mee naar de bundle, herschrijf hun
laadpaden met `install_name_tool` (van `/opt/homebrew/...` naar `@executable_path/...` of
`@rpath`), en sign alles mee.

Voordelen: exact dezelfde ffmpeg-versie/codecs als nu lokaal.
Nadelen: complexer, foutgevoelig (elke dylib heeft weer eigen dylibs → recursief), moet bij
elke ffmpeg-update opnieuw; meer kans op een volgende notarization-fail.

## Aanbeveling

**Optie A (static binaries).** Eenmalig iets meer setup, daarna nooit meer dit soort
dyld/Team-ID-gedoe. Belangrijk: vóór we het inbouwen 1× verifiëren dat de gekozen static
build `drawtext` (libfreetype) ondersteunt, want de caption-feature hangt daarvan af.

## Voorgestelde stappen (na akkoord)

1. Static arm64 ffmpeg + ffprobe ophalen (Martin-Riedl of npm-pakket), in repo onder
   `Omni DJ/vendor/ffmpeg/` of via download-stap in het script.
2. Verifiëren: `ffmpeg -version`, `otool -L` (geen externe dylibs), en `drawtext` aanwezig
   (`ffmpeg -filters | grep drawtext`).
3. `build_macos.sh` regels 120-122 aanpassen: kopieer de static binaries i.p.v. Homebrew.
4. (Optioneel maar aanbevolen) app.py/cutter.py de bundle-ffprobe expliciet laten gebruiken
   i.p.v. kaal `'ffprobe'`, met fallback naar PATH voor de dev-server.
5. `./build_macos.sh sign notarize dmg` opnieuw draaien.
6. Smoke-test: gesignde .app openen, een DJ-set uploaden, bevestigen dat analyse start.
7. DMG opnieuw uploaden naar `downloads.omnidj.com` (zelfde naam, overschrijft).

## Risico's / aandachtspunten

- Codec-dekking van static build (h264 encode/decode + drawtext) moet kloppen, anders faalt
  juist de cut/caption-stap i.p.v. de validatie.
- De huidige .app + DMG op R2 zijn dus nog NIET bruikbaar voor beta — vervangen na de fix.
- Universal (Intel+arm64) is later; voor nu arm64 volstaat voor Sjuul's eigen testers.

## Bronnen
- Static ffmpeg arm64 (signed/notarized): https://ffmpeg.martin-riedl.de/
- npm static pakket: https://www.npmjs.com/package/ffmpeg-ffprobe-static
- eugeneware/ffmpeg-static: https://github.com/eugeneware/ffmpeg-static
