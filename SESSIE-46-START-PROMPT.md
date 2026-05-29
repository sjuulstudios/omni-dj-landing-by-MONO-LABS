# Sessie 46 — Start-prompt

> Kopieer hieronder in een nieuwe chat om te starten.

---

## Voor jou (Sjuul) — vóór de chat begint

**Optioneel maar aanbevolen:** doe eerst de smoketests uit sessie 45 zelf (~15min in dev-server). Dan weet je of v2-shell werkt vóór we Fase 2 bouwen. Procedure staat in `HANDOVER.md` onder "STATUS NA SESSIE 45 → Wat Sjuul nog moet doen".

Als je het overslaat: ook prima, dan combineren we het in sessie 46.

---

## Plak dit in de nieuwe chat

```
Sessie 46 voor Clip Live. Lees als eerste:

1. HANDOVER.md (top — "STATUS NA SESSIE 45 — REDESIGN FASE 1")
2. PLAN-REDESIGN-MIGRATION-2026-05-26.md (sectie 2, vooral Fase 2)
3. clip-live-redesign-v2.html (mockup-referentie voor clips-grid)
4. LESSONS-LEARNED.md (vooral .app vs dev-server gedrag)

Status: redesign Fase 1 (sidebar + topbar shell) is code-side
klaar achter feature-flag `localStorage.clipLiveRedesignV2='1'`.
Sessie 43+44 ook code-side klaar.

Wat ik wil deze sessie:
- Fase 2: dashboard/clips-grid in v2-stijl
- Daarna: PyInstaller rebuild naar .app/.dmg

Mijn werkwijze:
- Eerst diagnose + plan + wachten op "ja"
- Daarna pas uitvoeren
- Backups vóór elke wijziging
- Minimale scope (alleen Fase 2, geen editor/modals deze sessie)
- Terminal-commando's letterlijk, zonder markdown-fences

Start met:
1. Bevestig dat je de huidige stand begrijpt (samenvat in 5 regels)
2. Stel verifiëringsvragen over Fase 2-scope (welke filter-chips,
   welke clip-card velden, hover-states)
3. Schrijf een Fase 2-plan in PLAN-REDESIGN-FASE2-2026-XX-XX.md
4. Wacht op mijn akkoord
5. Bouw → backup vooraf → verificeer JS-parse + HTML-balance → update HANDOVER.md
6. Daarna .app/.dmg rebuild-stappen voorbereiden (procedure)
```

---

## Bestanden die de assistent nodig heeft (referentie)

| Bestand | Waarvoor |
|---|---|
| `HANDOVER.md` | Huidige status, sessie 45 bovenaan |
| `PLAN-REDESIGN-MIGRATION-2026-05-26.md` | 5-fase migratieplan, Fase 2 specs |
| `PLAN-REDESIGN-2026-05-26.md` | Design-tokens, kleuren, typografie |
| `clip-live-redesign-v2.html` | Mockup van eindresultaat (in projectroot) |
| `dj-clip-cutter/static/index.html` | Live tool — gewijzigd in sessie 45 |
| `dj-clip-cutter/static/index.html.pre-redesign-v2.bak` | Rollback-backup |
| `LESSONS-LEARNED.md` | Bekende valkuilen, .app vs dev-server |
| `INSTALLER-RUNBOOK.md` | PyInstaller .app build procedure |
| `SESSIE43-EXPORT-PIPELINE-PLAN.md` | Voor context export-flow |

---

## Snelste rollback-instructie (als iets stuk gaat)

Plak letterlijk in Terminal:

cd "/Users/sjuulsmits/Documents/Claude/Projects/Clip Live/dj-clip-cutter" && cp static/index.html.pre-redesign-v2.bak static/index.html && ./start.sh

Dat zet de stand terug op vóór sessie 45 en herstart de dev-server.
