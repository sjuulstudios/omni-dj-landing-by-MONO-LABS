# Quota & Abonnementssysteem — Technische Rundown
_Gegenereerd op 2026-06-11_

## Hoe het systeem werkt

### Twee omgevingen

| Omgeving | Quota-route |
|---|---|
| Dev-server (`start.sh`) | `app.py` praat direct met Supabase via `supabase_admin` (service_role key) |
| Bundled `.app` (DMG) | Alle quota-calls gaan via de `update-usage` Edge Function met de JWT van de gebruiker |

### Flow bij een analyse

1. Gebruiker uploadt een bestand
2. `app.py` roept `_get_or_refresh_profile()` aan — leest `plan` en `usage_this_period` live uit Supabase
3. Als `used >= limit`: 402-response, analyse wordt geblokkeerd
4. Als toegestaan: analyse start
5. Na voltooiing: `_increment_usage()` verhoogt `usage_this_period` met 1 in Supabase

### Plan-limieten

Hardcoded in **twee** bestanden:

`app.py`:
```python
PLAN_LIMITS = {
    'free':   2,
    'pro':    10,
    'studio': float('inf'),
}
```

`supabase/functions/update-usage/index.ts`:
```typescript
const PLAN_LIMITS: Record<string, number> = {
  free: 2,
  pro: 10,
  studio: Number.POSITIVE_INFINITY,
};
```

### Hoe een plan-upgrade de app bereikt

Stripe stuurt een webhook naar de `stripe-webhook` Edge Function, die `profiles.plan` in Supabase updatet. De app leest dat veld live bij elke analyse — geen app-restart of lokale sync nodig.

Drie events worden afgehandeld:
- `checkout.session.completed` → zet plan + reset teller + nieuw 30-dagenvenster
- `customer.subscription.updated` → updatet plan
- `customer.subscription.deleted` → zet plan terug naar `'free'`

---

## Bevindingen & aandachtspunten

### 1. Limieten zijn hardcoded in twee bestanden (ACTIE VEREIST)

Als je de limieten per plan wil aanpassen (bijv. Pro van 10 naar 20), moet je:
- `app.py` aanpassen en een nieuwe DMG bouwen + uploaden naar R2
- De `update-usage` Edge Function opnieuw deployen

Gebruikers met de oude DMG hanteren de oude limieten totdat ze updaten.

**Aanbeveling op termijn:** limieten opslaan in een `plan_config`-tabel in Supabase zodat ze zonder app-update beheerbaar zijn.

### 2. Race condition bij gelijktijdige analyses

De quota-increment is een read-modify-write, geen atomische SQL-operatie. Als een gebruiker twee analyses tegelijk start (twee instanties), kunnen beide door de gate komen voordat de teller verhoogd is.

**Impact:** laag — lokale desktop-app, normaal gebruik heeft één instantie.
**Fix op termijn:** atomische Postgres RPC: `UPDATE profiles SET usage_this_period = usage_this_period + 1 RETURNING usage_this_period`.

### 3. Gate zit vóór analyse, increment ná voltooiing

Een gebruiker kan een derde analyse uploaden als de tweede nog bezig is (teller staat dan nog op 1). Na voltooiing van beide staat de teller op 2 resp. 3.

### 4. Downgrade reset de teller niet

Als een Pro-gebruiker (10 analyses) 8 analyses heeft gebruikt en downgradet naar Free (limiet 2), staat zijn teller op 8 en is hij direct geblokkeerd tot het 30-dagenvenster reset.

**Is dit gewenst gedrag?** Zo ja, geen actie. Zo nee: reset `usage_this_period` bij downgrade in `handleSubscriptionDeleted`.

### 5. Beveiliging in de bundled .app

De quota-teller staat in Supabase (niet lokaal), dus een gebruiker kan de teller niet resetten door een bestand aan te passen. Maar een technisch vaardige gebruiker kan de PyInstaller-bundle uitpakken en de gate-check in `app.py` verwijderen.

**Impact:** acceptabel voor een beta met kleine gebruikersgroep.
**Fix op termijn:** server-side analyse-token — de app vraagt vóór elke analyse een gesignde one-time token aan de Edge Function. Zonder geldige token start de analyse niet, ook niet als de lokale check is verwijderd.

---

## Directe actiepunten

Als je de limieten wil aanpassen of een bug wil fixen:

1. Pas `PLAN_LIMITS` aan in `app.py`
2. Pas `PLAN_LIMITS` aan in `supabase/functions/update-usage/index.ts`
3. Deploy de Edge Function:
   ```
   cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/Omni DJ"
   supabase functions deploy update-usage
   ```
4. Bouw een nieuwe DMG en upload naar R2

Beide bestanden moeten altijd in sync blijven.
