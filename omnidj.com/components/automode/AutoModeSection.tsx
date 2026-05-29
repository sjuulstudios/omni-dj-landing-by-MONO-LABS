'use client';

import React from 'react';
import Reveal from '@/components/ui/Reveal';
import RemotionMp4 from '@/components/ui/RemotionMp4';
import { autoModeContent } from '@/lib/content/automode';

export default function AutoModeSection() {
  const cssFallback = (
    <div
      className="grid grid-cols-1 md:grid-cols-5 gap-4 items-stretch w-full h-full"
      style={{ padding: 24 }}
    >
      <Stage><FileTile /></Stage>
      <ArrowCol />
      <Stage><AiTile /></Stage>
      <ArrowCol delay="1.5s" />
      <Stage><PostsTile /></Stage>
    </div>
  );

  return (
    <section className="section section-creme overflow-hidden">
      <div className="page-shell">
        <div className="max-w-[760px]">
          <Reveal>
            <h2 className="headline-section">{autoModeContent.headline}</h2>
          </Reveal>
        </div>

        {/* Looping animation — Remotion MP4 with CSS fallback */}
        <Reveal>
          <div className="mt-10 relative">
            <RemotionMp4
              src="/remotion/auto-mode.mp4"
              fallback={cssFallback}
              aspectRatio="16 / 5"
              style={{
                borderRadius: 24,
                background: 'transparent'
              }}
            />
          </div>
        </Reveal>

        {/* bullets — icons pulse in time with the pipeline animation above (one heartbeat) */}
        <Reveal delay={120}>
          <div className="mt-8 grid grid-cols-2 lg:grid-cols-4 gap-6">
            {autoModeContent.bullets.map((b, i) => (
              <div key={b.title}>
                <div className="flex items-center gap-2 mb-2">
                  <span
                    className="am-bullet-dot w-2 h-2 rounded-full"
                    style={{ background: 'var(--orange)', animationDelay: `${i * 0.75}s` }}
                    aria-hidden="true"
                  />
                  <h4 className="font-medium" style={{ color: '#0A0A0A' }}>{b.title}</h4>
                </div>
                <p className="text-[14px]" style={{ color: 'rgba(10,10,10,0.62)' }}>{b.body}</p>
              </div>
            ))}
          </div>
        </Reveal>

        {/* subline as an animated row of customisation tokens stacking onto the pipeline */}
        <Reveal delay={200}>
          <div className="mt-10 max-w-[680px]">
            <p className="body-default" style={{ color: 'rgba(10,10,10,0.62)' }}>Add customisation:</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {['Brand presets', 'Caption presets', 'Auto-tracking'].map((tok, i) => (
                <span
                  key={tok}
                  className="am-token text-[13px] font-medium px-3.5 py-1.5 rounded-full"
                  style={{
                    background: 'rgba(255,106,26,0.12)',
                    color: '#0A0A0A',
                    border: '1px solid rgba(255,106,26,0.4)',
                    animationDelay: `${i * 0.5}s`
                  }}
                >
                  {tok}
                </span>
              ))}
            </div>
          </div>
        </Reveal>
      </div>

      <style jsx>{`
        @keyframes amDot {
          0%   { transform: translateX(0); opacity: 0; }
          10%  { opacity: 1; }
          90%  { opacity: 1; }
          100% { transform: translateX(100%); opacity: 0; }
        }
        @keyframes amProgress {
          0%   { width: 0; }
          70%  { width: 100%; }
          100% { width: 100%; }
        }
        @keyframes amPostsIn {
          0%   { opacity: 0; transform: translateY(8px); }
          50%  { opacity: 1; transform: translateY(0); }
          100% { opacity: 1; transform: translateY(0); }
        }
        @keyframes amHeartbeat {
          0%, 100% { transform: scale(1); opacity: 0.55; }
          12%      { transform: scale(1.9); opacity: 1; }
          30%      { transform: scale(1); opacity: 0.55; }
        }
        @keyframes amTokenIn {
          0%   { opacity: 0; transform: translateY(6px); }
          18%  { opacity: 1; transform: translateY(0); }
          92%  { opacity: 1; transform: translateY(0); }
          100% { opacity: 1; transform: translateY(0); }
        }
        .am-bullet-dot {
          animation: amHeartbeat 3s var(--ease-drop) infinite;
        }
        .am-token {
          opacity: 0;
          animation: amTokenIn 3s var(--ease-drop) infinite;
        }
        @media (prefers-reduced-motion: reduce) {
          .am-bullet-dot { animation: none; opacity: 1; }
          .am-token { animation: none; opacity: 1; }
        }
      `}</style>
    </section>
  );
}

function Stage({ children }: { children: React.ReactNode }) {
  return (
    <div
      className="rounded-2xl p-6 flex flex-col justify-center min-h-[200px]"
      style={{
        background: 'rgba(10,10,10,0.04)',
        border: '1px solid rgba(10,10,10,0.08)'
      }}
    >
      {children}
    </div>
  );
}

function ArrowCol({ delay = '0s' }: { delay?: string }) {
  return (
    <div className="hidden md:flex items-center justify-center relative">
      <div className="relative w-full h-px" style={{ background: 'rgba(10,10,10,0.18)' }}>
        <span
          aria-hidden="true"
          className="absolute -top-[3px] left-0 w-2 h-2 rounded-full"
          style={{
            background: 'var(--orange)',
            animation: `amDot 3s linear ${delay} infinite`
          }}
        />
      </div>
    </div>
  );
}

function FileTile() {
  return (
    <div>
      <div
        className="rounded-lg p-4"
        style={{ background: 'var(--ink-900)', color: 'var(--creme)' }}
      >
        <div className="flex items-center gap-2 text-[12px]">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6"><path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" /><polyline points="14 3 14 9 20 9" /></svg>
          live_set.wav
        </div>
        <div className="mt-3 h-1.5 rounded-full overflow-hidden" style={{ background: 'rgba(245,239,227,0.12)' }}>
          <div
            className="h-full"
            style={{ background: 'var(--orange)', animation: 'amProgress 3s ease-out infinite' }}
          />
        </div>
        <div className="text-creme-mute text-[10px] mt-2">Analysing energy & drops</div>
      </div>
    </div>
  );
}

function AiTile() {
  return (
    <div
      className="rounded-lg p-4 relative overflow-hidden"
      style={{ background: 'var(--ink-900)', color: 'var(--creme)' }}
    >
      <div className="flex items-center justify-end">
        <span className="w-2 h-2 rounded-full" style={{ background: 'var(--orange)' }} />
      </div>
      <div className="mt-3 space-y-1.5">
        <div className="rounded-sm h-2" style={{ background: 'rgba(245,239,227,0.16)', width: '78%' }} />
        <div className="rounded-sm h-2" style={{ background: 'rgba(245,239,227,0.16)', width: '54%' }} />
        <div className="rounded-sm h-2" style={{ background: 'rgba(245,239,227,0.16)', width: '88%' }} />
      </div>
      <div className="text-[10px] mt-3 text-creme-mute">Captions · Brand · Crop</div>
    </div>
  );
}

function PostsTile() {
  const labels = ['Instagram', 'TikTok', 'YouTube'];
  return (
    <div className="space-y-2">
      {labels.map((l, i) => (
        <div
          key={l}
          className="flex items-center gap-3 p-3 rounded-lg"
          style={{
            background: 'var(--ink-900)',
            color: 'var(--creme)',
            animation: `amPostsIn 3s ease-out ${1 + i * 0.4}s infinite`,
            opacity: 0
          }}
        >
          <div className="w-6 h-6 rounded placeholder-box" style={{ borderRadius: 4, border: 0, background: 'rgba(245,239,227,0.14)' }} />
          <div className="text-[12px] flex-1">
            <div className="font-medium">{l}</div>
            <div className="text-creme-mute text-[10px]">Scheduled</div>
          </div>
          <span className="text-[10px]" style={{ color: 'var(--orange)' }}>●</span>
        </div>
      ))}
    </div>
  );
}
