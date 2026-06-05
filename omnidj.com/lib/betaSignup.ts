import { SUPABASE_URL, SUPABASE_ANON_KEY } from '@/lib/config';

/**
 * Send a beta signup straight to Supabase (insert-only table beta_signups).
 *
 * Resolves true on success and false on any failure. It never throws, so the
 * caller can decide what the UI shows. A duplicate email is treated as success
 * so we do not leak whether an address was already on the list.
 */
export async function submitBetaSignup(email: string, source = 'site'): Promise<boolean> {
  const clean = email.trim();
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(clean)) return false;

  try {
    const res = await fetch(`${SUPABASE_URL}/rest/v1/beta_signups`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        apikey: SUPABASE_ANON_KEY,
        Authorization: `Bearer ${SUPABASE_ANON_KEY}`,
        // The insert-only policy has no SELECT, so ask PostgREST not to echo the
        // new row back (returning it would otherwise fail with a 401).
        Prefer: 'return=minimal'
      },
      body: JSON.stringify({ email: clean, source })
    });
    // 201 = inserted, 409 = duplicate email (already on the list) — both fine.
    return res.status === 201 || res.status === 409;
  } catch {
    return false;
  }
}
