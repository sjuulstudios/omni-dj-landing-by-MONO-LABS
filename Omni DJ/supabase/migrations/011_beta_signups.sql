-- 011_beta_signups.sql
-- SESSIE 76 (2026-06-04) — beta-aanmeldingen vanaf de marketingsite (omnidj.com).
--
-- De site is een statische export (Cloudflare Pages) en kan zelf geen servercode
-- draaien. In plaats van een externe dienst (Formspree) posten de formulieren
-- rechtstreeks naar deze tabel met de PUBLIEKE anon-key. Dat is veilig omdat de
-- RLS hieronder alleen INSERT toestaat: anon/authenticated kunnen een rij
-- toevoegen, maar de lijst NOOIT uitlezen, wijzigen of verwijderen. Alleen de
-- service_role (Supabase-dashboard) ziet de inhoud.

create table if not exists public.beta_signups (
  id         uuid primary key default gen_random_uuid(),
  email      text not null,
  source     text not null default 'site',
  created_at timestamptz not null default now()
);

-- Dedupe op e-mail (case-insensitief). Een dubbele aanmelding geeft een nette
-- 409 die de frontend als 'gelukt' behandelt (lekt niet of een adres al bestond).
create unique index if not exists beta_signups_email_key
  on public.beta_signups (lower(email));

alter table public.beta_signups enable row level security;

-- Alleen INSERT toestaan, met een simpele e-mail-sanity-check. Geen SELECT/UPDATE/
-- DELETE policy => die zijn geweigerd voor anon/authenticated.
drop policy if exists beta_signups_insert on public.beta_signups;
create policy beta_signups_insert on public.beta_signups
  for insert to anon, authenticated
  with check (
    email ~* '^[^@\s]+@[^@\s]+\.[^@\s]+$'
    and char_length(email) <= 254
  );

-- Expliciet: alleen INSERT-recht, geen SELECT. (Supabase geeft public-tabellen
-- standaard ruime grants; hier strak zetten zodat alleen toevoegen kan.)
revoke all on public.beta_signups from anon, authenticated;
grant insert on public.beta_signups to anon, authenticated;
