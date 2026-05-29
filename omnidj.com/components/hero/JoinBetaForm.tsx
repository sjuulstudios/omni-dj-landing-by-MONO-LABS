'use client';

import React, { useState } from 'react';

export default function JoinBetaForm({ placeholder, label }: { placeholder: string; label: string }) {
  const [email, setEmail] = useState('');
  const [state, setState] = useState<'idle' | 'sending' | 'done' | 'error'>('idle');

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.includes('@')) return;
    setState('sending');
    try {
      await fetch('/api/beta-signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      }).catch(() => null);
      setState('done');
    } catch {
      setState('error');
    }
  };

  const done = state === 'done';

  return (
    <div style={{ position: 'relative', overflow: 'hidden', borderRadius: 999 }}>
      {/* Form row — slides out to the left on success */}
      <form
        onSubmit={submit}
        aria-hidden={done}
        className="flex items-center gap-2 pl-5 pr-2 py-2 rounded-full border border-creme-line bg-black"
        style={{
          transform: done ? 'translateX(-110%)' : 'translateX(0)',
          opacity: done ? 0 : 1,
          transition: 'transform 480ms var(--ease-drop), opacity 320ms var(--ease-drop)',
          pointerEvents: done ? 'none' : 'auto'
        }}
      >
        <input
          type="email"
          value={email}
          onChange={e => setEmail(e.target.value)}
          placeholder={placeholder}
          aria-label="Email for beta signup"
          required
          className="flex-1 bg-transparent border-0 outline-none py-2 text-creme placeholder:text-creme-mute text-[14px] min-w-0"
        />
        <button
          type="submit"
          disabled={state === 'sending'}
          aria-label={label}
          className="flex-shrink-0 h-9 w-9 rounded-full bg-orange text-ink flex items-center justify-center transition-all disabled:opacity-50"
          style={{ background: 'var(--orange)' }}
        >
          {state === 'sending' ? (
            <span className="beta-spin" aria-hidden="true" />
          ) : (
            <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M5 12h14M13 6l6 6-6 6" />
            </svg>
          )}
        </button>
      </form>

      {/* Success badge — slides in from the right */}
      <div
        aria-live="polite"
        className="flex items-center justify-center gap-2 px-5 py-4 rounded-full"
        style={{
          position: done ? 'relative' : 'absolute',
          inset: done ? undefined : 0,
          background: 'rgba(255,106,26,0.10)',
          border: '1px solid var(--orange)',
          color: 'var(--creme)',
          transform: done ? 'translateX(0)' : 'translateX(110%)',
          opacity: done ? 1 : 0,
          transition: 'transform 480ms var(--ease-drop), opacity 320ms var(--ease-drop)',
          pointerEvents: done ? 'auto' : 'none'
        }}
      >
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="var(--orange)" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <polyline points="20 6 9 17 4 12" />
        </svg>
        <span className="text-[14px] font-medium">You are on the list. We will be in touch.</span>
      </div>

      <style jsx>{`
        .beta-spin {
          display: block;
          width: 14px;
          height: 14px;
          border: 2px solid rgba(0, 0, 0, 0.3);
          border-top-color: var(--ink);
          border-radius: 50%;
          animation: betaSpin 0.7s linear infinite;
        }
        @keyframes betaSpin {
          to { transform: rotate(360deg); }
        }
        @media (prefers-reduced-motion: reduce) {
          .beta-spin { animation-duration: 1.2s; }
        }
      `}</style>
    </div>
  );
}
