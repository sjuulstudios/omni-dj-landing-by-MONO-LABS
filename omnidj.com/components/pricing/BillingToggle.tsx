'use client';

import React from 'react';

export default function BillingToggle({
  value,
  onChange
}: {
  value: 'monthly' | 'yearly';
  onChange: (v: 'monthly' | 'yearly') => void;
}) {
  return (
    <div
      className="inline-flex items-center gap-1 p-1 rounded-full"
      style={{ background: 'rgba(245,239,227,0.06)', border: '1px solid var(--creme-line)' }}
      role="radiogroup"
    >
      {(['monthly', 'yearly'] as const).map(v => {
        const active = v === value;
        return (
          <button
            key={v}
            role="radio"
            aria-checked={active}
            onClick={() => onChange(v)}
            className="px-5 py-2 rounded-full text-[13px] font-medium transition-all"
            style={{
              background: active ? 'var(--creme)' : 'transparent',
              color: active ? 'var(--ink)' : 'var(--creme-mute)'
            }}
          >
            {v === 'monthly' ? 'Monthly' : 'Yearly'}
            {v === 'yearly' && (
              <span
                className="ml-2 text-[10px] px-1.5 py-0.5 rounded-full"
                style={{
                  background: active ? 'var(--orange)' : 'rgba(255,106,26,0.18)',
                  color: active ? 'var(--ink)' : 'var(--orange)'
                }}
              >
                15% off
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
