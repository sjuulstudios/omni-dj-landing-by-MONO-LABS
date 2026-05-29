'use client';

import React from 'react';
import Link from 'next/link';
import MegaIcon from '@/components/nav/MegaIcon';
import type { MegaGroup } from '@/lib/content/megamenu';

type Props = {
  open: boolean;
  columns: MegaGroup[];
  onMouseEnter?: () => void;
  onMouseLeave?: () => void;
  onItemClick?: () => void;
};

export default function MegaMenu({ open, columns, onMouseEnter, onMouseLeave, onItemClick }: Props) {
  return (
    <div
      role="region"
      aria-hidden={!open}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      className="absolute left-1/2 top-full z-40"
      style={{
        transform: `translateX(-50%) translateY(${open ? 0 : -6}px)`,
        opacity: open ? 1 : 0,
        pointerEvents: open ? 'auto' : 'none',
        transition: 'opacity 240ms var(--ease-drop), transform 240ms var(--ease-drop)',
        marginTop: 8
      }}
    >
      <div
        className="rounded-2xl"
        style={{
          background: 'rgba(10, 10, 10, 0.94)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          border: '1px solid var(--creme-line)',
          /* Crafted multi-layer shadow instead of a single hard shadow-2xl. */
          boxShadow:
            '0 24px 24px rgba(0,0,0,0.08), 0 32px 48px rgba(0,0,0,0.04), 0 64px 96px rgba(0,0,0,0.02)',
          padding: 24,
          minWidth: columns.length === 3 ? 760 : 560,
          maxWidth: '90vw'
        }}
      >
        <div
          className="grid gap-2"
          style={{ gridTemplateColumns: `repeat(${columns.length}, minmax(0, 1fr))` }}
        >
          {columns.map((col, ci) => (
            <div key={ci} className="flex flex-col">
              {col.title && (
                <div
                  className="eyebrow text-creme-mute mb-3 px-3"
                  style={{ fontSize: 10, letterSpacing: '0.14em' }}
                >
                  {col.title}
                </div>
              )}
              <div className="flex flex-col gap-1">
                {col.items.map((item, ii) => (
                  <Link
                    key={ii}
                    href={item.href}
                    onClick={onItemClick}
                    className="group flex items-start gap-3 p-3 rounded-xl transition-colors"
                    style={{
                      opacity: item.soon ? 0.55 : 1
                    }}
                    onMouseEnter={e => {
                      (e.currentTarget as HTMLElement).style.background = 'rgba(245,239,227,0.06)';
                    }}
                    onMouseLeave={e => {
                      (e.currentTarget as HTMLElement).style.background = 'transparent';
                    }}
                  >
                    <span
                      className="flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center"
                      style={{
                        background: 'rgba(245,239,227,0.06)',
                        color: 'var(--creme)'
                      }}
                    >
                      <MegaIcon kind={item.icon} />
                    </span>
                    <span className="flex-1 min-w-0">
                      <span className="flex items-center gap-2">
                        <span className="text-creme font-medium text-[14px]">{item.title}</span>
                        {item.soon && (
                          <span
                            className="text-[10px] px-1.5 py-0.5 rounded-full font-medium"
                            style={{
                              background: 'rgba(255,106,26,0.16)',
                              color: 'var(--orange)'
                            }}
                          >
                            soon
                          </span>
                        )}
                      </span>
                      <span className="block text-creme-mute text-[12px] mt-0.5 leading-[1.45]">
                        {item.body}
                      </span>
                    </span>
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
