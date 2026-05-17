# Clip Live — Installer Runbook

Hoe je Clip Live verpakt als downloadbare app voor klanten.
Geschreven voor Sjuul (niet-technisch). Werk dit van boven naar beneden af.
Sla niets over zonder mij te vragen.

---

## Wat is er nu in het project klaargezet

In de map dj-clip-cutter/ staan vier nieuwe bestanden:

- **launcher.py** — desktop entry point, opent automatisch je browser
- **ClipLive.spec** — recept voor PyInstaller
- **entitlements.plist** — Apple toestemming-bestand voor signing
- **build_macos.sh** — één commando dat de hele build doet

Plus dit document.

App.py is niet aangepast.

---

## Fase 1 — Eerste testbuild (unsigned, ~30 minuten)

Hier maak je een werkende .app waarmee jij zelf kunt testen of de bundle
draait. Geen Apple account nodig. Klanten kunnen 'm wel openen maar zien
een Gatekeeper-waarschuwing — niet voor distributie geschikt.

**Stap 1 — Open Terminal en ga naar de juiste map**

cd "/Users/sjuulsmits/Documents/Claude/Projects/Clip Live/dj-clip-cutter"

Wat dit doet: zet Terminal in de projectmap.

**Stap 2 — Activeer je Python virtuele omgeving**

source venv/bin/activate

Wat dit doet: schakelt over naar de Python die alle Clip Live dependencies
heeft. Je prompt krijgt (venv) ervoor.

**Stap 3 — Installeer PyInstaller en dmgbuild**

pip install pyinstaller dmgbuild

Wat dit doet: voegt twee tools toe — PyInstaller bouwt de .app, dmgbuild
maakt later de .dmg.

**Stap 4 — Eerste testbuild**

./build_macos.sh

Wat dit doet: bouwt dist/Clip Live.app. Duurt 3–8 minuten. Je ziet veel
output — dat is normaal. Als het stopt zonder "FOUT" ben je klaar.

**Stap 5 — Test of de app draait**

open "dist/Clip Live.app"

Wat dit doet: opent je nieuwe app. Browser moet vanzelf openen op
http://127.0.0.1:5555. Als dat werkt, ga je naar Fase 2.

**Stap 6 — Als macOS klaagt: "kan niet worden geopend"**

Dat is verwacht zonder signing. Workaround alleen voor jezelf:
rechtsklik op de .app → Open → bevestig in het popupje.

---

## Fase 2 — Apple Developer account regelen (eenmalig, $99/jaar)

Zonder dit kun je geen distributable .app maken. Klanten krijgen anders
de Gatekeeper-blokkade en haken af.

**Stap 1** — Ga naar https://developer.apple.com/programs/enroll/

**Stap 2** — Meld je aan als Sole Proprietor (eenmanszaak). Apple vraagt:
- Apple ID (gebruik business@sjuulstudios.com)
- KVK-nummer (92316476)
- DUNS-nummer — Apple vraagt het alleen voor bedrijven, voor eenmanszaak
  in NL meestal niet nodig
- Creditcard voor de $99 jaarlijkse fee

Doorlooptijd: 24 uur tot 5 werkdagen. Apple verifieert je identiteit.

**Stap 3** — Eenmaal goedgekeurd, maak een "Developer ID Application"
certificaat aan in https://developer.apple.com/account/resources/certificates/list

Download het .cer bestand en dubbelklik om in je Keychain te zetten.

**Stap 4** — Vind je certificaat-naam:

security find-identity -v -p codesigning

Wat dit doet: laat alle Developer ID certificaten in je Keychain zien.
Kopieer de regel die begint met "Developer ID Application: Sjuul Studios".

**Stap 5** — Zet die naam in je shell-profiel zodat je 'm niet steeds
hoeft te typen:

echo 'export APPLE_DEVELOPER_ID="Developer ID Application: Sjuul Studios (TEAMID)"' >> ~/.zshrc

Vervang TEAMID door je echte team ID die in het certificaat staat. Open
een nieuwe Terminal-tab zodat de variabele actief is.

---

## Fase 3 — Notarization profiel (eenmalig)

Notarization is een tweede Apple-stap die Gatekeeper expliciet vertelt
"deze app is goedgekeurd". Zonder dit krijgt elke gebruiker nog steeds
een waarschuwing bij de eerste opening.

**Stap 1** — Maak een app-specifiek wachtwoord aan:
https://appleid.apple.com → Sign In and Security → App-Specific Passwords → +
Naam: cliplive-notary. Kopieer het wachtwoord — Apple toont het maar één keer.

**Stap 2** — Sla het wachtwoord op in je Keychain:

xcrun notarytool store-credentials cliplive-notary --apple-id business@sjuulstudios.com --team-id TEAMID --password APP-SPECIFIC-PASSWORD

Vervang TEAMID en APP-SPECIFIC-PASSWORD door je echte waarden. Dit hoef
je maar één keer te doen.

**Stap 3** — Zet de profielnaam in je shell-profiel:

echo 'export APPLE_NOTARY_PROFILE=cliplive-notary' >> ~/.zshrc

Nieuwe Terminal-tab openen.

---

## Fase 4 — Volledig getekende en genotarizeerde build

Dit is de build die je naar klanten kunt sturen.

cd "/Users/sjuulsmits/Documents/Claude/Projects/Clip Live/dj-clip-cutter"
source venv/bin/activate
./build_macos.sh sign notarize dmg

Wat dit doet: bouwt, signt, stuurt op voor notarization (1–15 min wachten
op Apple), staple't de notarization aan de app, en maakt een .dmg.

Resultaat: dist/Clip Live.dmg — dat is het bestand dat je op clipdroplive.com
zet als downloadlink.

---

## Fase 5 — Windows .exe (later)

Windows kan je niet vanaf je Mac bouwen. Drie opties:

1. **Parallels / VMware met Windows 11** op je Mac. ~€100 plus Windows
   licentie. Dan dezelfde flow met PyInstaller maar zonder build_macos.sh.
2. **GitHub Actions** met windows-latest runner — bouwt en signt
   automatisch bij elke release. Gratis tot 2000 minuten per maand.
3. **Een tweede Windows-machine** waar je af en toe op werkt.

Windows code-signing certificaat kost €100–400/jaar, bv. via SSL.com of
DigiCert. Zonder certificaat krijgt elke Windows-gebruiker een
SmartScreen-waarschuwing.

Mijn aanbeveling: begin met **alleen macOS**. Win11 + signing kan in
fase 2 als macOS-versie loopt.

---

## Wat KLANTEN doen om Clip Live te installeren

1. Klik op de Download-knop op clipdroplive.com → Clip Live.dmg downloadt
2. Dubbelklik de .dmg → er opent een venster met de app en een
   "Applications" pijl
3. Sleep Clip Live.app naar de Applications-snelkoppeling
4. Open de app uit Applications
5. Hun browser opent automatisch op http://127.0.0.1:5555

Bij eerste opening (na notarization): geen waarschuwing. Bij elke daarna:
direct gebruik.

---

## Checklist voor je eerste echte release

Loop dit lijstje af voordat je de .dmg op de website zet:

- [ ] Fase 1: testbuild draait lokaal
- [ ] App opent browser automatisch
- [ ] Upload + drop-detectie werkt in de bundle
- [ ] FFmpeg-gebaseerde export werkt
- [ ] Stripe-checkout werkt vanuit de bundle (live mode)
- [ ] Apple Developer account actief
- [ ] Signing werkt (geen Gatekeeper-blokkade op je Mac)
- [ ] Notarization slaagt
- [ ] DMG opent op een tweede Mac (vraag een vriend)
- [ ] Privacy/terms aanvullingen live op clipdroplive.com
- [ ] Download-link op site wijst naar de gestaple'de .dmg

---

## Bekende valkuilen

- **Bundle is groot** (verwacht 400–700 MB door librosa+scipy+numba). Niet
  in te krimpen zonder zware deps eruit te halen — dan werkt drop-detectie
  niet meer.
- **Eerste opening duurt 10–30 sec** terwijl numba modules JIT-compileert.
  Dit is normaal en gebeurt alleen de eerste keer.
- **.env is NIET in de bundle** — dat is opzettelijk. De gebundelde
  Stripe/Supabase keys moeten via een config in je bundel komen of door
  user-input. Volgende klus: hard-code de production publishable keys
  (alleen pk_live_…) en verwijder secret keys uit de bundle.
- **AntiVirus op Windows** flagt ongetekende PyInstaller bundles vaak als
  malware. Reden waarom signing op Windows écht nodig is.
