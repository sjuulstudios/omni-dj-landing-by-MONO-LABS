'use client';

import React from 'react';

type Group = { title: string; rows: string[][] };

function renderCell(v: string) {
  if (v === '✓') return <span style={{ color: 'var(--orange)' }}>✓</span>;
  if (v === '—') return <span style={{ color: 'var(--creme-mute)' }}>—</span>;
  if (v === 'soon') return (
    <span
      className="text-[10px] px-2 py-0.5 rounded-full font-medium"
      style={{ background: 'rgba(255,106,26,0.16)', color: 'var(--orange)' }}
    >
      soon
    </span>
  );
  return <span className="text-creme text-[13px]">{v}</span>;
}

const TIER_NAMES = ['Free', 'Pro', 'Studio', 'Studio+'];

export default function PricingMatrix({ groups }: { groups: Group[] }) {
  return (
    <div
      className="rounded-3xl overflow-hidden"
      style={{
        background: 'var(--ink-900)',
        border: '1px solid var(--creme-line)'
      }}
    >
      {/* Header */}
      <div
        className="grid items-center text-[11px] tracking-[0.12em] uppercase font-medium"
        style={{
          gridTemplateColumns: '2fr repeat(4, 1fr)',
          padding: '20px 28px',
          color: 'var(--creme-mute)',
          borderBottom: '1px solid var(--creme-line)',
          background: 'rgba(245,239,227,0.02)'
        }}
      >
        <div>Feature</div>
        {TIER_NAMES.map(n => <div key={n} className="text-center">{n}</div>)}
      </div>

      {groups.map(g => (
        <div key={g.title}>
          <div
            className="text-[11px] tracking-[0.12em] uppercase font-medium"
            style={{
              color: 'var(--orange)',
              padding: '24px 28px 10px',
              background: 'rgba(255,106,26,0.04)'
            }}
          >
            {g.title}
          </div>
          {g.rows.map((row, ri) => (
            <div
              key={ri}
              className="grid items-center text-[14px]"
              style={{
                gridTemplateColumns: '2fr repeat(4, 1fr)',
                padding: '16px 28px',
                borderTop: '1px solid var(--creme-line)',
                color: 'var(--creme)'
              }}
            >
              <div>{row[0]}</div>
              {row.slice(1).map((c, ci) => (
                <div key={ci} className="text-center">{renderCell(c)}</div>
              ))}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
