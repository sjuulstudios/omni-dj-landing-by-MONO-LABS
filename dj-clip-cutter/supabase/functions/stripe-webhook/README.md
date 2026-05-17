# Stripe webhook — Supabase Edge Function

Mirrors Stripe subscription events into the `profiles` table so Clip Live
sees plan changes the moment Stripe confirms a payment.

## Deploy (eerste keer)

Vereist: Supabase CLI (`brew install supabase/tap/supabase`) en `supabase login`.

Vanuit `/Users/sjuulsmits/Documents/Claude/Projects/Clip Live/dj-clip-cutter`:

1. **Init eenmalig** (alleen als `supabase/config.toml` nog niet bestaat):

   supabase init

2. **Link aan het juiste project:**

   supabase link --project-ref lbabsffxefkrxwzkbzar

3. **Zet de secrets** (vervang `<…>` door echte waardes; `--env-file` kan handiger zijn):

   supabase secrets set STRIPE_SECRET_KEY=sk_test_…
   supabase secrets set STRIPE_WEBHOOK_SECRET=whsec_…
   supabase secrets set STRIPE_PRICE_ID_PRO=price_1TUoYNA5DKhJaSAF6xynooY9
   supabase secrets set STRIPE_PRICE_ID_STUDIO=price_1TUoZCA5DKhJaSAFI7AMgAbA
   supabase secrets set SUPABASE_SERVICE_ROLE_KEY=eyJ…

   `SUPABASE_URL` en `SUPABASE_ANON_KEY` worden automatisch door de runtime
   gezet — niet zelf invullen.

4. **Deploy**:

   supabase functions deploy stripe-webhook --no-verify-jwt

   `--no-verify-jwt` is verplicht: Stripe stuurt zijn eigen handtekening
   (`stripe-signature`), geen Supabase JWT.

5. **Endpoint registreren in Stripe**:

   - Open dashboard.stripe.com → Developers → Webhooks → "Add endpoint".
   - URL = `https://lbabsffxefkrxwzkbzar.supabase.co/functions/v1/stripe-webhook`
   - Events:
     - `checkout.session.completed`
     - `customer.subscription.updated`
     - `customer.subscription.deleted`
     - `invoice.payment_failed` (optioneel, alleen voor logging)
   - Klik op de zojuist aangemaakte endpoint → "Signing secret" → kopieer
     het `whsec_…` token. Plak die in stap 3 als `STRIPE_WEBHOOK_SECRET`
     en zet ook in `dj-clip-cutter/.env` als `STRIPE_WEBHOOK_SECRET=…`.

## Updates deployen

   supabase functions deploy stripe-webhook --no-verify-jwt

(Geen wijziging in secrets nodig tenzij je sleutels hebt geroteerd.)

## Logs bekijken

   supabase functions logs stripe-webhook

Live tail tijdens een testkaart-checkout met `4242 4242 4242 4242`.

## Test (zonder dashboard)

Stripe CLI lokaal:

   stripe trigger checkout.session.completed

Dat fuzzt een nep-event naar je live endpoint — handig voor smoke-tests
zonder echt een checkout te doen. CLI-events hebben geen `metadata.user_id`
dus de handler logt een waarschuwing en stopt — dat is verwacht gedrag.
