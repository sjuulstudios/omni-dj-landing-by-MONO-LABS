# Sessie 31 start-prompt

Kopieer onderstaand blok als eerste bericht in de nieuwe sessie:

---

Lees /Users/sjuulsmits/Documents/Claude/Projects/Clip Live/HANDOVER.md, in het bijzonder het blok "TWEE OPENSTAANDE BUGS - HOOGSTE PRIORITEIT VOOR SESSIE 31" bovenaan. Server draait op http://127.0.0.1:5555 via ./start.sh in /Users/sjuulsmits/Documents/Claude/Projects/Clip Live/dj-clip-cutter. Test-DJ-sets staan in /Users/sjuulsmits/Documents/Claude/Projects/Clip Live/dj-clip-cutter/CLIP DROP DJ-SETS/ - werk met Lisa Korver x Hör Berlin.mp4. Je hebt mijn akkoord om de Chrome connector te gebruiken om de tool live te testen.

Ik wil dat je deze twee bugs oplost, in volgorde:

**BUG 1 - BPM/Key corner stamp moet WEG.**
Op de preview én op de geëxporteerde clip zie ik rechtsboven "144 BPM · 4B" staan. Ik wil dit volledig verwijderen, voor preview en export. Niet als toggle laten staan - gewoon weg. Dit zit in cutter.py via een drawtext / brand-stamp flow.

**BUG 2 - "Follow horizontally" zoomt nog steeds in.**
Als ik op Follow horizontally klik (de pan-mode in de Track-drawer), zoomt hij nog steeds in. Ik wil dat de video van **boven tot onder de hele preview vult** - dus volle hoogte zichtbaar - en dat het beeld alleen horizontaal mee-pant met de DJ. Links/rechts mogen zwarte balken zijn als de aspect ratio dat vereist. Geen zoom, niks afsnijden van boven of onder.

Mogelijke oorzaak voor bug 2 staat in HANDOVER.md: de Lisa Korver source is mogelijk al portrait (1080×1920), waardoor de pan-crop berekening (`pan_w = src_h * 9/16`) breder uitkomt dan src_w en de pan-mode terugvalt op de bestaande vertical-crop. Eerst even ffprobe draaien op de bron om dit te verifiëren.

Aanpak die ik wil:
1. Diagnose eerst - lees HANDOVER, ffprobe op Lisa Korver source, lees `_build_tracked_vertical_crop` en `_build_vertical_cmd` in cutter.py, lees waar BPM-stamp wordt gerendered
2. Stel een fix voor per bug en wacht op mijn "ja" - DAN pas implementeren
3. Live test via Chrome MCP nadat je de fix hebt
4. HANDOVER updaten aan het einde

Sjuul is niet-technisch - terminal-commando's letterlijk zonder markdown fences, één commando per regel met pad-quotes. Begin met diagnose + voorstel, wacht op ja, dan los werken.

---
