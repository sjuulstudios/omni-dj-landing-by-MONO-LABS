# Supabase migrations — Clip Live / Clip Drop

Deze map bevat de SQL-migrations die de Supabase-staat van Clip Drop
beschrijven. Tot sessie 32 leefden alle RLS-policies en triggers alleen in
het Supabase Dashboard. Vanaf nu staat de waarheid hier, in version control.

## Wat staat hier

| File | Datum | Wat |
|---|---|---|
| `001_rls_policies.sql` | 2026-05-23 | RLS aan op `profiles` + select/update policies + kolom-bescherming |

## Hoe pas je deze toe?

Er zijn twee paden — kies wat het beste voelt.

### Pad A — Supabase Dashboard SQL Editor (aanbevolen voor jou)

Geen extra tools nodig, werkt vanuit je browser.

1. Open https://supabase.com/dashboard/project/lbabsffxefkrxwzkbzar
2. Linker menu: **SQL Editor** (icoontje met `>_`)
3. Klik **New query** rechtsboven
4. Open lokaal `001_rls_policies.sql`, kopieer de **hele** inhoud
5. Plak in de SQL Editor
6. Lees de comments bovenaan even door zodat je weet wat er gebeurt
7. Klik **Run** (of cmd+enter)
8. Resultaat: "Success. No rows returned." — dat is goed; CREATE POLICY geeft geen rijen terug

### Pad B — Supabase CLI (technisch, optioneel)

Je hebt al de CLI omdat je `supabase functions deploy` gebruikt:

cd "/Users/sjuulsmits/Documents/Claude/Projects/Clip Live/dj-clip-cutter"

Dan:

supabase db push

NB: `supabase db push` kijkt naar alle files in deze folder en past ze in
volgorde toe. Voor je eerste keer kun je beter Pad A doen — dan zie je per
statement of het slaagt.

## Verificatie na uitvoeren

Plak deze 2 queries één voor één in dezelfde SQL Editor en run:

### 1. Staat RLS aan?

select schemaname, tablename, rowsecurity from pg_tables where schemaname = 'public' and tablename = 'profiles';

Verwacht: één rij met `rowsecurity = true`.

### 2. Bestaan de policies?

select polname, polcmd from pg_policy where polrelid = 'public.profiles'::regclass order by polname;

Verwacht: 2 rijen:
- `Users can read own profile` met `polcmd = r` (SELECT)
- `Users can update own profile (safe columns)` met `polcmd = w` (UPDATE)

## Live test (optioneel, maar wel grondig)

Als je een test-account hebt (bv. `business+wftest17@sjuulstudios.com` uit
sessie 17), kun je deze test doen in de SQL Editor:

1. Haal eerst je test-user UUID op:

select id from auth.users where email = 'business+wftest17@sjuulstudios.com';

2. Vervang `:uid` hieronder door die UUID en run één voor één:

begin;
set local role authenticated;
set local request.jwt.claim.sub = ':uid';

-- 2a. SELECT moet alleen eigen rij teruggeven
select id, plan, usage_this_period from public.profiles;

-- 2b. Veilige update moet slagen
update public.profiles set artist_name = 'TEST RLS' where id = ':uid';

-- 2c. Gevoelige update moet FALEN
update public.profiles set plan = 'studio' where id = ':uid';

rollback;  -- zet alles terug, dit was alleen een test

Verwacht bij stap 2c: foutmelding zoals
`new row violates row-level security policy for table "profiles"`.

Als die foutmelding NIET komt, dan accepteert de policy een plan-upgrade
door de user zelf — dat is een gat. Stuur me een screenshot.

## Wat als ik per ongeluk iets stuk maak

Onderaan `001_rls_policies.sql` staat een ROLLBACK-blok, commented out.
Uncomment het en run dat in de SQL Editor. RLS blijft staan; alleen de
policies worden verwijderd. Daarna ben je terug bij waar je vóór de
migration zat.

## Volgende migrations

Als je later policies wilt toevoegen voor een nieuwe tabel (bv. een
`jobs`-tabel voor cloud-sync), maak je een nieuwe file in deze folder:
`002_<korte beschrijving>.sql`. Houd ze klein en focus 1 thema per file.
