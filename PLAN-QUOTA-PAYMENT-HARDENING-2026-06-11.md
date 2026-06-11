# PLAN: Quota + payment system hardening
_2026-06-11. Status: PROPOSAL, waiting for go-ahead. Nothing is built yet._

This plan consolidates the findings from both rundowns (the English security review and the Dutch quota rundown) into one coherent change set across three places: Supabase, the `update-usage` edge function, and `app.py` (plus a small webhook tweak). It also answers the mid-analysis upgrade question with a concrete design and a test you can run.

Per the project workflow: this is the diagnosis and proposed approach. I will not touch any file until you say go, and I will then do it in small steps, one at a time.

---

## 1. The issues we are bringing together

| # | Issue | Source | Severity | Where the fix lives |
|---|---|---|---|---|
| A | Gate runs before analysis, counter increments only after completion, so parallel starts slip through | quota #3 | Medium | Supabase + app.py |
| B | Counter is read-modify-write, not atomic, so it can drift / undercount | quota #2, sec M2 | Medium | Supabase + edge fn |
| C | Plan limits hardcoded in two files, must stay in sync, needs a rebuild to change | quota #1 | Medium | Supabase (new table) |
| D | Downgrade does not reset the counter, a downgraded user can be instantly blocked | quota #4 | Low, policy | webhook |
| E | A technical user can unpack the bundle and delete the local gate | quota #5, sec L5 | Accepted for beta | edge fn (one-time token, later) |
| F | Mid-analysis upgrade: what happens to counting when the plan changes while a set is analysing | new question | Design | app.py + test |
| G | Possible XSS if user text (captions, filenames, brand text) is ever rendered with innerHTML | sec M3 | Verify | frontend audit |
| H | Stripe still in test mode, generic-error polish | sec L1, L2 | Launch checklist | config + app.py |

The thing to hold onto: the analysis is local DSP, it costs you nothing per run. So this work is about correctness and revenue protection, not compute cost. We are buying "the free tier is a real nudge and the paid features the server controls are truly enforced," not "nobody can ever bypass it."

---

## 2. Target design (the end state)

1. One source of truth for limits. A `plan_config` table in Supabase holds `plan` and `monthly_limit`. The edge function reads it. `app.py` reads it (cached) instead of its own hardcoded dict. Changing a limit becomes a single SQL update, no DMG rebuild.

2. The server owns the count, atomically. A Postgres function (RPC) does the reserve and the release in one statement so there is no race and no "passed the gate but never counted" gap.

3. Reserve at start, finalise or release at end. When an analysis is accepted we reserve a slot up front (this is what actually blocks parallel starts). If the analysis fails we release it. If it succeeds we keep it. Each job has a stable id so the reserve and the release are idempotent (a job can never be counted twice or released twice).

4. Upgrades only ever help the user. Counting is tied to the job, not re-evaluated against a moving plan. An in-flight analysis that started under one plan always finishes. See Section 4.

5. Downgrade policy is explicit and intentional (Section 5 decision).

6. Optional, post-beta: a one-time signed analysis grant so an honest build cannot start an analysis without the server's yes, even if the local check is patched out.

---

## 3. Phased implementation

Each phase is independently shippable and testable. I would do them in this order.

### Phase 1 (Supabase): atomic counter + config table

New migration `012_quota_atomic.sql`:

1. `plan_config` table: `plan text primary key`, `monthly_limit int` (NULL means unlimited). Seed it with free=2, pro=10, studio=NULL. RLS: readable by `authenticated` and `anon` (it is not secret), writable only by service_role.

2. `quota_reservations` table (or a column approach): `job_id text primary key`, `user_id uuid`, `created_at`, `state text` (reserved / finalised / released). This gives per-job idempotency that survives across processes and a mid-flight plan change.

3. Postgres function `reserve_quota(p_user uuid, p_job text)`:
   - rolls the 30-day window if expired (same logic as today),
   - reads the user's plan and its limit from `plan_config`,
   - if there is already a reservation for `p_job`, returns the existing decision (idempotent),
   - else if `usage_this_period < limit` (or limit is NULL), inserts a reservation, bumps `usage_this_period` by 1, returns `{allowed:true, used, limit, ...}` in one atomic statement,
   - else returns `{allowed:false, used, limit, reset_in_days}`.

4. Postgres function `release_quota(p_user uuid, p_job text)`: if a reservation for `p_job` is in state reserved, set it to released and decrement `usage_this_period` by 1 (floor at 0). Idempotent.

This is the core of fixes A and B. Reserving inside one SQL statement means two parallel starts cannot both see "room for one."

### Phase 2 (edge function): rewrite `update-usage`

- Replace the JS `PLAN_LIMITS` constant with a read from `plan_config`.
- Replace the read-modify-write increment with calls to the new RPCs.
- New actions: `reserve` (job_id) and `release` (job_id) alongside the existing `get`. Keep `increment` as a thin alias to `reserve` for backward compatibility with older DMGs in the field, so we do not strand beta users on the old bundle.
- Keep JWT verification required (unchanged).

### Phase 3 (app.py): reserve-at-start, finalise/release-at-end

- In `/api/upload` and `/api/upload-local`, replace the current "read profile, check used >= limit" gate with a single `reserve` call (direct RPC via `supabase_admin` in dev, or via the edge function in the bundle). Pass the job id. If not allowed, return the existing 402 body.
- Remove the hardcoded `PLAN_LIMITS` dict in favour of the server decision. Keep a tiny fallback only for the offline/degraded case.
- In `_process_job`: on failure or empty result, call `release` (idempotent). On success, do nothing extra because the slot was already reserved. Remove the old end-of-job `_increment_usage`. Keep the `usage_counted` style idempotency but keyed on job id at the server.
- `/api/quota` keeps reporting used/limit from the same snapshot the RPC returns, so the UI is unchanged.

### Phase 4 (webhook): downgrade policy

Depends on your decision in Section 5. If we reset on downgrade, add `usage_this_period: 0` and a fresh window to `handleSubscriptionDeleted` (and optionally to `subscription.updated` when the plan moves down).

### Phase 5: mid-analysis upgrade handling + test (Section 4)

### Phase 6 (launch checklist, not blocking the above)

- Swap Stripe test keys for live, rotate the webhook signing secret, re-test the webhook end to end.
- Generic client-facing error strings (stop echoing exception text).
- Grep the frontend for `innerHTML` and confirm captions, filenames, artist/brand text and hashtags are written as text, not HTML (fix G).
- Decide the pricing reframe: which paid features are server-controlled (publishing, scheduling, cloud sync, teams) and therefore the real enforceable moat.

---

## 4. Mid-analysis upgrade: what happens, and how we make it correct

### What happens today

Free user, `used = 1`, limit 2. They start analysis number two (a long set, several minutes). The gate sees 1 < 2 and lets it run. While it runs they buy Pro. Stripe fires `checkout.session.completed`, the webhook sets `plan = pro` and resets `usage_this_period = 0` with a new 30-day window. The analysis finishes and `_increment_usage` reads the now-reset 0 and writes 1.

Net result today: it already works out in the user's favour. They end up Pro, counter at 1, lots of room. There is no double charge of "tokens" because there are no tokens, only a per-month set counter. The only real risks are mechanical:

- a race between the webhook reset and the end-of-job increment (both touch `usage_this_period`),
- the increment reading a stale value,
- and, once we move to reserve-at-start, a reservation that the reset wipes out.

### The policy we should commit to

Policy: an analysis is gated by the plan at the moment it is accepted. Once accepted it always completes, regardless of any plan change during the run. Upgrades take effect for the next analysis. This is simple, predictable, and always favours the user.

### How the new design handles it cleanly

Because counting is tied to the job id (the reservation), a plan change mid-run cannot double-count or wrongly block:

- We reserved the slot at start under Free. The job is recorded in `quota_reservations`.
- `checkout.session.completed` resets `usage_this_period` to 0. That simply wipes the in-flight reservation's contribution, which is fine: the user upgraded, they get a clean window.
- On completion we do not increment again (the slot was reserved, not incremented at the end), so there is no race with the webhook reset.
- On failure we call `release` keyed by job id, which is idempotent and floors at 0, so even after a reset it cannot push the counter negative.

One refinement to decide: whether `checkout.session.completed` should keep resetting `usage_this_period` to 0. With reserve-at-start, a reset mid-run is harmless and generous. I recommend keeping the reset, since a paying user expects a fresh allowance.

### How to test it (this is the "way to check" you asked for)

I will add an automated test that does not need real Stripe or a real card. Two layers:

1. SQL/RPC unit test (fastest, deterministic). Seed a profile Free, used=1. Call `reserve(job=A)` -> allowed, used becomes 2. Simulate the webhook by running the same UPDATE the webhook runs (plan=pro, usage=0, new window). Then call the completion path (no end increment) and `reserve(job=B)` -> allowed under Pro. Assert: final plan=pro, counter consistent, user not blocked, job A counted at most once. Also test the failure path: `reserve(job=A)` then `release(job=A)` after a reset -> counter never goes below 0.

2. End-to-end on the dev server (:5599), scripted, no card needed. Start a deliberately slow analysis, then directly POST the same profile mutation the webhook performs (or use a Stripe test-clock / the Stripe CLI `stripe trigger checkout.session.completed` against the test webhook). Assert the analysis still finishes, the UI flips to Pro, and the next upload is allowed. I will write this as a small pytest plus a shell runner, matching how earlier sessions verified things on :5599.

I will capture the expected vs actual counter at each step so you can see it is correct, rather than just asserting pass/fail.

---

## 5. Decisions (CONFIRMED 2026-06-11)

1. Downgrade behaviour (issue D): RESET to 0. On downgrade the counter resets to 0 with a fresh window, so the user can immediately use their lower-tier allowance. Phase 4 will add `usage_this_period: 0` + new window to `handleSubscriptionDeleted` (and to `subscription.updated` when the plan moves down).

2. One-time signed analysis grant (issue E): DEFER to post-beta. Not built now. We lean on the pricing reframe (server-controlled paid features) plus the signed bundle for the beta. The edge function and RPC design leave room to add it later without rework.

3. Limits (issue C): KEEP free=2, pro=10, studio=unlimited. Same values as today, just moved into `plan_config` so they are editable without a rebuild.

---

## 6. Deploy / rebuild checklist (for when we ship)

1. Apply migration 012 to Supabase (via branch + the existing cross-account RLS audit harness, then merge).
2. `supabase functions deploy update-usage`.
3. Update `app.py`, run the static + logic checks, test on :5599 logged in.
4. Build a new signed + notarized DMG, upload to R2 as `Omni-DJ-1.0.0.dmg` (website unchanged).
5. Run the mid-analysis-upgrade test from Section 4 and save the output.
6. Keep `plan_config` as the only place limits change from now on, no rebuild needed for limit tweaks.

Note: older DMGs in the field keep working because the edge function keeps the `increment`/`get` actions as compatibility aliases. They just will not get the parallel-start fix until the user updates, which is acceptable for beta.
