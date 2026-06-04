-- 006_workspaces_rls.sql
-- SESSIE 71 (2026-06-02) — RLS voor workspaces + workspace_members (A1).
--
-- !!! REVIEW ONLY — NOG NIET TOEGEPAST. Branch + audit-harness eerst (zie 005). !!!
--
-- HOOGSTE-RISICO-STAP: dit is de data-isolatie tussen artists/workspaces. De
-- policies leunen op auth.uid(), dus ze werken ALLEEN als de backend deze
-- tabellen via de anon-client + user-JWT bevraagt (PLAN v1.3, Correctie 6).
-- De membership-checks gaan via de SECURITY DEFINER helpers uit 005 om
-- RLS-recursie op workspace_members te vermijden.
--
-- Verplicht vóór merge naar main: audit/AUDIT_cross_account_rls.sql groen
-- (2 users x 2 workspaces, geen enkele lek).

-- ---------------------------------------------------------------------------
-- workspaces
-- ---------------------------------------------------------------------------
alter table public.workspaces enable row level security;

drop policy if exists workspaces_select on public.workspaces;
create policy workspaces_select on public.workspaces
  for select using (
    owner_id = auth.uid() or public.is_workspace_member(id)
  );

-- Je mag alleen een workspace aanmaken die JIJ bezit. De app dwingt daarnaast
-- profiles.max_workspaces af (FREE/Solo 1, Studio later) vóór de insert.
drop policy if exists workspaces_insert on public.workspaces;
create policy workspaces_insert on public.workspaces
  for insert with check (
    owner_id = auth.uid()
  );

drop policy if exists workspaces_update on public.workspaces;
create policy workspaces_update on public.workspaces
  for update using (public.is_workspace_owner(id))
  with check (public.is_workspace_owner(id));

drop policy if exists workspaces_delete on public.workspaces;
create policy workspaces_delete on public.workspaces
  for delete using (public.is_workspace_owner(id));

-- ---------------------------------------------------------------------------
-- workspace_members
-- ---------------------------------------------------------------------------
alter table public.workspace_members enable row level security;

-- Members zien hun mede-members (om het roster te tonen).
drop policy if exists members_select on public.workspace_members;
create policy members_select on public.workspace_members
  for select using (
    public.is_workspace_member(workspace_id)
  );

-- Alleen de owner nodigt uit. (De owner-as-member trigger draait als definer
-- en valt buiten RLS, dus de bootstrap-insert botst hier niet mee.)
drop policy if exists members_insert on public.workspace_members;
create policy members_insert on public.workspace_members
  for insert with check (
    public.is_workspace_owner(workspace_id)
  );

drop policy if exists members_update on public.workspace_members;
create policy members_update on public.workspace_members
  for update using (public.is_workspace_owner(workspace_id))
  with check (public.is_workspace_owner(workspace_id));

-- Owner verwijdert leden; een lid mag zichzelf verwijderen (workspace verlaten).
drop policy if exists members_delete on public.workspace_members;
create policy members_delete on public.workspace_members
  for delete using (
    public.is_workspace_owner(workspace_id) or user_id = auth.uid()
  );
