import React from 'react';
import { AbsoluteFill, Easing, interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { COLORS, FONT_FAMILY } from '../colors';

/**
 * Tool Overview — three-hour set -> drops detected -> reframed -> shorts queued.
 *
 * Premium pass: a single playhead sweeps the waveform, drops fire a pulse + label
 * as it crosses them, the reframe fan springs open, and the shorts pop in with a
 * spring. A step rail at the top makes the active stage explicit. 10s clean loop.
 *
 * Signature easing "The Drop" = cubic-bezier(0.16, 1, 0.3, 1).
 */
const DROP = Easing.bezier(0.16, 1, 0.3, 1);

export const ToolOverviewFlow: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const loop = frame % durationInFrames;
  const t = loop / fps; // seconds in the 10s loop

  // Stage windows
  const playhead = interpolate(t, [0.3, 4], [0, 1], { easing: Easing.linear, extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const fanOpen = interpolate(t, [4.2, 6], [0, 1], { easing: DROP, extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const shortsIn = interpolate(t, [6.4, 8.4], [0, 1], { easing: DROP, extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  // Which stage is "active" for the step rail
  const stage = t < 4 ? 0 : t < 6.2 ? 1 : 2;

  const con1 = interpolate(t, [3.9, 4.6], [0, 1], { easing: DROP, extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const con2 = interpolate(t, [6.0, 6.7], [0, 1], { easing: DROP, extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  return (
    <AbsoluteFill style={{ background: COLORS.ink, fontFamily: FONT_FAMILY, padding: 56, display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: 28 }}>
      <StepRail stage={stage} />

      <div style={{ position: 'relative', width: '100%', display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 48, alignItems: 'stretch' }}>
        <NodeShell index={0} label="Analyse" title="Your set" subtitle="live_set_amsterdam_2024.wav · 3:00:00" active={stage === 0}>
          <Waveform playhead={playhead} t={t} />
        </NodeShell>

        <NodeShell index={1} label="Reframe" title="Every feed, one pass" subtitle="9:16 · 1:1 · 4:5" active={stage === 1}>
          <ReframeFan progress={fanOpen} />
        </NodeShell>

        <NodeShell index={2} label="Publish" title="Shorts ready" subtitle="TikTok · Instagram · YouTube" active={stage === 2}>
          <ShortsStack progress={shortsIn} frame={frame} fps={fps} />
        </NodeShell>

        {/* Tight directional arrows between nodes (draw in) */}
        <svg aria-hidden style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none' }} viewBox="0 0 1600 430" preserveAspectRatio="none">
          <Arrow x={508} progress={con1} />
          <Arrow x={1052} progress={con2} />
        </svg>
      </div>
    </AbsoluteFill>
  );
};

const StepRail: React.FC<{ stage: number }> = ({ stage }) => {
  const steps = ['Analyse', 'Reframe', 'Publish'];
  return (
    <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
      {steps.map((s, i) => {
        const active = i === stage;
        const done = i < stage;
        return (
          <React.Fragment key={s}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span
                style={{
                  width: 22, height: 22, borderRadius: 11, display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 11, fontWeight: 600,
                  background: active || done ? COLORS.orange : 'rgba(245,239,227,0.08)',
                  color: active || done ? COLORS.ink : COLORS.cremeMute,
                  transition: 'all 200ms'
                }}
              >
                {i + 1}
              </span>
              <span style={{ fontSize: 13, fontWeight: 500, color: active ? COLORS.creme : COLORS.cremeMute }}>{s}</span>
            </div>
            {i < steps.length - 1 && <span style={{ flex: '0 0 40px', height: 1, background: 'rgba(245,239,227,0.14)' }} />}
          </React.Fragment>
        );
      })}
    </div>
  );
};

const Arrow: React.FC<{ x: number; progress: number }> = ({ x, progress }) => {
  const cy = 215;
  return (
    <g opacity={progress}>
      <line x1={x} y1={cy} x2={x + 36 * progress} y2={cy} stroke={COLORS.orange} strokeWidth={2} />
      <path d={`M ${x + 30} ${cy - 6} L ${x + 40} ${cy} L ${x + 30} ${cy + 6}`} fill="none" stroke={COLORS.orange} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" opacity={progress > 0.6 ? 1 : 0} />
    </g>
  );
};

const NodeShell: React.FC<{ index: number; label: string; title: string; subtitle: string; active: boolean; children: React.ReactNode }> = ({
  label, title, subtitle, active, children
}) => (
  <div
    style={{
      background: COLORS.ink900,
      border: `1px solid ${active ? 'rgba(255,106,26,0.4)' : COLORS.cremeLine}`,
      borderRadius: 20,
      padding: 28,
      display: 'flex',
      flexDirection: 'column',
      boxShadow: active ? '0 0 0 1px rgba(255,106,26,0.2)' : 'none',
      transition: 'border-color 250ms'
    }}
  >
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 18 }}>
      <span style={{ fontSize: 11, letterSpacing: 2, textTransform: 'uppercase', color: active ? COLORS.orange : COLORS.cremeMute, fontWeight: 600 }}>{label}</span>
    </div>
    <div style={{ fontSize: 18, fontWeight: 500, color: COLORS.creme, marginBottom: 18 }}>{title}</div>
    <div style={{ marginBottom: 18, flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 150 }}>{children}</div>
    <div style={{ fontSize: 12, color: COLORS.cremeMute, fontFeatureSettings: '"tnum" 1' }}>{subtitle}</div>
  </div>
);

const BAR_COUNT = 56;
const DROP_BARS = [Math.round(0.35 * (BAR_COUNT - 1)), Math.round(0.78 * (BAR_COUNT - 1))];

const Waveform: React.FC<{ playhead: number; t: number }> = ({ playhead, t }) => {
  const bars = Array.from({ length: BAR_COUNT }, (_, i) => {
    const x = i / (BAR_COUNT - 1);
    const v = 0.18 + 0.22 * Math.sin(x * 6.28)
      + 0.45 * Math.exp(-Math.pow((x - 0.35) * 8, 2))
      + 0.55 * Math.exp(-Math.pow((x - 0.78) * 7, 2));
    return Math.round(Math.max(8, Math.min(110, v * 110)));
  });

  return (
    <div style={{ position: 'relative', display: 'flex', alignItems: 'flex-end', gap: 4, height: 130, width: '100%' }}>
      {bars.map((h, i) => {
        const passed = i / (BAR_COUNT - 1) <= playhead;
        const isDrop = DROP_BARS.includes(i);
        return (
          <div key={i} style={{ flex: 1, height: h, borderRadius: 2, background: isDrop ? COLORS.orange : passed ? 'rgba(245,239,227,0.7)' : 'rgba(245,239,227,0.3)' }} />
        );
      })}

      {/* Drop labels that pop as the playhead crosses */}
      {DROP_BARS.map((db, i) => {
        const dx = db / (BAR_COUNT - 1);
        const crossed = playhead >= dx;
        const pulse = crossed ? (Math.sin((t - dx * 4) * 6) + 1) / 2 : 0;
        return (
          <div key={i} style={{ position: 'absolute', left: `${dx * 100}%`, top: -6, transform: 'translateX(-50%)', opacity: crossed ? 1 : 0, transition: 'opacity 200ms' }}>
            <span style={{ display: 'block', fontSize: 9, letterSpacing: 1, color: COLORS.orange, fontWeight: 700, whiteSpace: 'nowrap', transform: `scale(${1 + pulse * 0.12})` }}>DROP</span>
          </div>
        );
      })}

      <div style={{ position: 'absolute', top: -2, bottom: 0, left: `${playhead * 100}%`, width: 2, background: COLORS.creme }} />
    </div>
  );
};

const ReframeFan: React.FC<{ progress: number }> = ({ progress }) => {
  const variants = [
    { w: 38, h: 66, label: '9:16' },
    { w: 52, h: 52, label: '1:1' },
    { w: 48, h: 58, label: '4:5' }
  ];
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
      <div style={{ width: 130, height: 74, borderRadius: 8, background: COLORS.ink800, border: `1px solid ${COLORS.cremeLine}`, display: 'flex', alignItems: 'center', justifyContent: 'center', color: COLORS.cremeMute, fontSize: 11, letterSpacing: 1.4 }}>
        16:9
      </div>
      {/* fan lines */}
      <svg width="40" height="74" viewBox="0 0 40 74" style={{ opacity: progress }}>
        <path d="M0 37 L40 10" stroke={COLORS.orange} strokeWidth={1.5} />
        <path d="M0 37 L40 37" stroke={COLORS.creme} strokeWidth={1.5} opacity={0.5} />
        <path d="M0 37 L40 64" stroke={COLORS.creme} strokeWidth={1.5} opacity={0.5} />
      </svg>
      <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
        {variants.map((v, i) => {
          const a = Math.max(0, Math.min(1, progress * 3 - i * 0.6));
          return (
            <div key={v.label} style={{ width: v.w, height: v.h, borderRadius: 7, background: COLORS.ink800, border: `1px solid rgba(255,106,26,${0.35 * a})`, display: 'flex', alignItems: 'center', justifyContent: 'center', color: COLORS.cremeMute, fontSize: 9, letterSpacing: 1, opacity: a, transform: `translateY(${(1 - a) * 12}px)` }}>
              {v.label}
            </div>
          );
        })}
      </div>
    </div>
  );
};

const ShortsStack: React.FC<{ progress: number; frame: number; fps: number }> = ({ progress, frame, fps }) => {
  const platforms = ['TT', 'IG', 'YT'];
  return (
    <div style={{ display: 'flex', alignItems: 'flex-end', gap: 12 }}>
      {[0, 1, 2].map(i => {
        const local = Math.max(0, Math.min(1, progress * 3 - i * 0.55));
        const pop = spring({ frame: frame - (6.4 + i * 0.4) * fps, fps, config: { damping: 14, mass: 0.6 }, durationInFrames: 30 });
        const scale = local > 0 ? 0.9 + pop * 0.1 : 0.9;
        const h = 96 + i * 6;
        return (
          <div key={i} style={{ width: 58, height: h, borderRadius: 9, background: COLORS.ink800, border: `1px solid rgba(255,106,26,${0.3 * local})`, position: 'relative', opacity: local, transform: `translateY(${(1 - local) * 12}px) scale(${scale})` }}>
            <span style={{ position: 'absolute', top: 7, left: 7, fontSize: 9, fontWeight: 700, color: i === 0 ? COLORS.orange : COLORS.cremeMute }}>{platforms[i]}</span>
            <span style={{ position: 'absolute', bottom: 8, left: 7, right: 7, height: 3, borderRadius: 2, background: i === 0 ? COLORS.orange : 'rgba(245,239,227,0.2)' }} />
          </div>
        );
      })}
    </div>
  );
};
