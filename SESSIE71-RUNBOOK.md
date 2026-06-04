# Sessie 71 - runbook + smoketest (2026-06-02)

> Wat deze sessie code-side is gebouwd, hoe je het test, en wat bewust NIET is aangeraakt.
> Niets is gecommit of herbouwd (sandbox kan niet committen). Jij doet git + rebuild zelf.
> Geen em-dashes/en-dashes. Terminalregels staan letterlijk; paden met spaties altijd tussen quotes.

## 1. Wat er is gebouwd (code-side, getest met py_compile + node --check + SQL-parser)

1. **Plan v1.3 (kritische review).** In `PLAN-COMBINED-DATA-LAYER-PLUS-ELECTRON-2026-06-02.md` sectie 9b.
   Belangrijkste vondst: de backend draait alles via de service_role-key en omzeilt RLS. De multi-tenant
   data-isolatie (A1) moet daarom via de anon-client + user-JWT, anders beschermt RLS niets. Plus 9 kleinere
   correcties en een aangepaste bouwvolgorde.

2. **C1 - Editor als eigen sidebar-tab.** Nieuwe "Editor" tussen Library en Brand. Klik je hem aan zonder
   geladen clip, dan zie je een kiezer (Continue editing van je laatste sessie + een grid met recente sets +
   een Import-knop) in plaats van een leeg scherm. Frontend-only, raakt de pipeline niet.

3. **C2 - Import.** Een Import-knop in de Editor-toolbar, in de Editor-leegstaat en in de Library-header.
   Hij trekt een losse video (mp4/mov/m4v/webm) rechtstreeks de tool in: het bestand wordt lokaal opgeslagen,
   geprobed (duur/afmetingen), krijgt een thumbnail en opent meteen in de editor voor trim/captions/brand/export.
   Geen analyse nodig. Nieuw, additief endpoint `/api/import-clip`; bestaande analyse/export-code is niet gewijzigd.
   (Audio-import komt later met de audio-sync-feature, Spoor D.)

4. **A1-migraties als review-bestanden (NIET toegepast).** `supabase/migrations/005-009*.sql` + de verplichte
   audit-harness `supabase/audit/AUDIT_cross_account_rls.sql`. Geschreven met de gecorrigeerde anon+JWT+RLS-
   architectuur. Deze raken de live database NIET tot jij/ik ze op een branch toepast en de audit groen is.

Bewust UITGESTELD: C7 (Settings opschonen). Settings heeft te veel JS-gebonden controls om blind te
herstructureren zonder live test; dat doen we in een sessie waar we de dev-server kunnen draaien.

## 2. Eerst: smoketest dat de kernfuncties nog werken (op je Mac)

De dev-server start je zo (let op: de oude HANDOVER noemde nog `dj-clip-cutter`, die map bestaat niet meer):

cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/Omni DJ" && ./start.sh

Dat start Flask lokaal. Open daarna in je browser:

http://127.0.0.1:5555

Loop deze lijst af. Als 1 t/m 4 werken, is de kern intact:

1. **Auth.** Inloggen werkt en is oranje (V2). Na een tijdje doorgebruiken blijf je ingelogd (token-refresh).
2. **Analyse.** Sleep of kies een echte DJ-set. Analyse draait, drops verschijnen. (Geen dubbele clips.)
3. **Edit.** Open een clip in de editor. Preview speelt, scrubben werkt, Trim werkt.
4. **Export.** Exporteer met captions aangevinkt. Er komt een MP4 op schijf en de captiontekst staat in beeld.

## 3. Daarna: de nieuwe features testen

**C1 - Editor-tab:**
- Klik in de sidebar op "Editor" terwijl er geen clip open is. Je hoort de kiezer te zien (Continue editing +
  recente sets). Klik een recente set: die opent in de editor.
- Open een clip, ga weg en terug: de Editor-tab licht op als je in de editor bent.

**C2 - Import:**
- Klik "Import" (Editor-toolbar of Library-header), kies een korte mp4. Hij hoort te uploaden, een toast
  "Clip imported" te geven en direct in de editor te openen. Trim en Export horen op die clip te werken.
- Test ook een .mov. Een niet-video (bv. .txt) hoort netjes geweigerd te worden met een melding.

Als iets hapert: het Import-endpoint is nieuw en is niet live getest (de sandbox kan je Mac-pipeline niet
draaien). Meld wat je ziet, dan fix ik het gericht.

## 4. A1 (multi-tenant) - NIET zomaar toepassen

De migraties 005-009 staan klaar maar mogen pas live als dit pad is gevolgd (zie plan sectie 9b):

1. Maak een Supabase-branch (geisoleerd van productie).
2. Pas 005 t/m 009 daarop toe, in volgorde.
3. Draai `supabase/audit/AUDIT_cross_account_rls.sql` op die branch. Je moet twee keer "AUDIT OK" zien en geen
   enkele EXCEPTION. Dit bewijst dat artist A de data van artist B niet ziet.
4. Pas daarna pas: backend ombouwen zodat de nieuwe tabellen via de anon-client + user-JWT gaan (niet via
   service_role), en de workspace-scope aanzetten. Pas als dat ook getest is, merge je naar main.

Wil je dat ik dit op een branch doe? Zeg het, dan zet ik stap 1 t/m 3 voor je klaar. (Een branch kan een
kleine Supabase-kost hebben; daarom vraag ik het eerst.)

## 5. Git (jij doet dit zelf)

Mijn wijzigingen stapelen bovenop de nog-niet-gecommitte sessie-69-wijzigingen (file-picker-fix + V1->V2).
Conform plan sectie 8 gaan ze samen in EEN commit. Gewijzigde/nieuwe bestanden deze sessie:

- Omni DJ/app.py (nieuw: /api/import-clip)
- Omni DJ/static/index.html (C1 + C2)
- supabase/migrations/005_workspaces.sql t/m 009_scheduled_posts.sql (review)
- supabase/audit/AUDIT_cross_account_rls.sql (review)
- PLAN-COMBINED-DATA-LAYER-PLUS-ELECTRON-2026-06-02.md (v1.3)
- SESSIE71-RUNBOOK.md (dit bestand)
- Backups: Omni DJ/static/index.html.pre-sessie71.bak, Omni DJ/app.py.pre-sessie71.bak

Pas een gesignde rebuild + DMG-naar-R2 NA de smoketest van de sessie-69 file-picker-fix (harde voorwaarde uit
de HANDOVER). De nieuwe features hierboven zijn dev-server-getest werk; de bundle-rebuild blijft jouw stap.
