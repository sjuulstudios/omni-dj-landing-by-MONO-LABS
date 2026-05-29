'use client';

import React, { useState } from 'react';

const roles = [
  'DJ',
  'Talent manager',
  'Videographer or editor',
  'Event organiser',
  'Record label',
  'Other'
];

export default function ContactForm() {
  const [state, setState] = useState<'idle' | 'sending' | 'done' | 'error'>('idle');
  const [data, setData] = useState({
    name: '',
    email: '',
    role: roles[0],
    company: '',
    message: ''
  });

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!data.email.includes('@') || !data.message) return;
    setState('sending');
    try {
      await fetch('/api/contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      }).catch(() => null);
      setState('done');
    } catch {
      setState('error');
    }
  };

  if (state === 'done') {
    return (
      <div
        className="rounded-3xl p-10 text-center"
        style={{ background: 'var(--ink-900)', border: '1px solid var(--creme-line)' }}
      >
        <div className="text-[40px] mb-3">✓</div>
        <h2 className="headline-h3 text-creme">Thanks.</h2>
        <p className="mt-3 body-default text-creme-mute">
          We will be in touch within 2 business days.
        </p>
      </div>
    );
  }

  // Progressive disclosure: name + role appear only once the visitor starts
  // typing their message, keeping the resting state to 2 fields.
  const expanded = data.message.length > 0;

  return (
    <form
      onSubmit={submit}
      className="space-y-5 rounded-3xl p-8"
      style={{ background: 'var(--ink-900)', border: '1px solid var(--creme-line)' }}
    >
      <Field label="Email" required>
        <input
          type="email"
          required
          placeholder="you@email.com"
          value={data.email}
          onChange={e => setData({ ...data, email: e.target.value })}
          className="form-input"
        />
      </Field>

      <Field label="What are you working on?" required>
        <textarea
          required
          rows={5}
          placeholder="Tell us a little about you and what you need."
          value={data.message}
          onChange={e => setData({ ...data, message: e.target.value })}
          className="form-input"
          style={{ minHeight: 130 }}
        />
      </Field>

      {/* Revealed only after the visitor commits to writing a message. */}
      <div
        className="contact-reveal"
        style={{
          maxHeight: expanded ? 220 : 0,
          opacity: expanded ? 1 : 0,
          overflow: 'hidden',
          transition: 'max-height 420ms var(--ease-drop), opacity 320ms var(--ease-drop)'
        }}
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 pt-1">
          <Field label="Name">
            <input
              value={data.name}
              onChange={e => setData({ ...data, name: e.target.value })}
              className="form-input"
            />
          </Field>
          <Field label="Role">
            <select
              value={data.role}
              onChange={e => setData({ ...data, role: e.target.value })}
              className="form-input"
            >
              {roles.map(r => <option key={r}>{r}</option>)}
            </select>
          </Field>
        </div>
      </div>

      <button
        type="submit"
        disabled={state === 'sending'}
        className="btn btn-orange w-full"
        style={{ width: '100%' }}
      >
        {state === 'sending' ? 'Sending…' : 'Send'}
        {state !== 'sending' && (
          <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M5 12h14M13 6l6 6-6 6" />
          </svg>
        )}
      </button>

      {state === 'error' && (
        <p className="text-[13px]" style={{ color: 'var(--orange)' }}>
          Something went wrong. Please try again or email us directly.
        </p>
      )}

      <style jsx>{`
        :global(.form-input) {
          width: 100%;
          background: rgba(245, 239, 227, 0.04);
          border: 1px solid var(--creme-line);
          border-radius: 12px;
          padding: 14px 16px;
          color: var(--creme);
          font-size: 15px;
          transition: border-color 200ms;
        }
        :global(.form-input:focus) {
          outline: none;
          border-color: var(--orange);
        }
        :global(.form-input::placeholder) {
          color: var(--creme-mute);
        }
      `}</style>
    </form>
  );
}

function Field({
  label,
  required,
  children
}: {
  label: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <label className="block">
      <span className="block eyebrow mb-2">
        {label}
        {required && <span style={{ color: 'var(--orange)' }}> *</span>}
      </span>
      {children}
    </label>
  );
}
