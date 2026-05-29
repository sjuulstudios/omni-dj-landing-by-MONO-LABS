import React from 'react';
import { AbsoluteFill, Easing, interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { COLORS, FONT_FAMILY } from '../colors';

/**
 * Auto-mode — watch-folder drop -> automatic processing -> scheduled posts.
 *
 * Premium pass: no "AI" text label (removed per brand direction). The middle
 * stage reads as an automatic processing step (progress bars + chips). Posts
 * spring in. Tighter vertical rhythm so it sits close to the bullets below.
 * Creme background to match the section-creme variant. 8s clean loop.
 */
const DROP = Easing.bezier(0.16, 1, 0.3, 1);

export const AutoModePipeline: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const loop = frame % durationInFrames;
  const t = loop / fps; // seconds in the 8s loop

  const fileProgress = interpolate(t, [0.3, 3.4], [0, 1], { easing: DROP, extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const arrow1 = interpolate(t, [3.2, 4.0], [0, 1], { easing: DROP, extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const procProgress = interpolate(t, [4.0, 5.4], [0, 1], { easing: DROP, extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const arrow2 = interpolate(t, [5.2, 6.0], [0, 1], { easing: DROP, extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  return (
    <AbsoluteFill style={{ background: COLORS.creme, fontFamily: FONT_FAMILY, padding: 56, display: 'flex', alignItems: 'center' }}>
      <div style={{ width: '100%', display: 'grid', gridTemplateColumns: '1fr 72px 1fr 72px 1fr', gap: 28, alignItems: 'stretch' }}>
        <Stage label="Watch-folder">
          <FileTile progress={fileProgress} />
        </Stage>

        <ArrowStage progress={arrow1} />

        <Stage label="Auto-process">
          <ProcessTile progress={procProgress} t={t} />
        </Stage>

        <ArrowStage progress={arrow2} />

        <Stage label="Scheduled">
          <PostsTile frame={frame} fps={fps} />
        </Stage>
      </div>
    </AbsoluteFill>
  );
};

const Stage: React.FC<{ label: string; children: React.ReactNode }> = ({ label, children }) => (
  <div style={{ background: 'rgba(10,10,10,0.04)', border: '1px solid rgba(10,10,10,0.08)', borderRadius: 20, padding: 22, display: 'flex', flexDirection: 'column', gap: 14, minHeight: 240, justifyContent: 'center' }}>
    <span style={{ fontSize: 10, letterSpacing: 2, textTransform: 'uppercase', color: 'rgba(10,10,10,0.5)', fontWeight: 600 }}>{label}</span>
    {children}
  </div>
);

const ArrowStage: React.FC<{ progress: number }> = ({ progress }) => (
  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
    <div style={{ position: 'relative', width: '100%', height: 2, background: 'rgba(10,10,10,0.16)' }}>
      <div style={{ position: 'absolute', top: -5, left: `${progress * 100}%`, width: 12, height: 12, borderRadius: 6, background: COLORS.orange, transform: 'translateX(-50%)', boxShadow: '0 0 0 4px rgba(255,106,26,0.18)' }} />
    </div>
  </div>
);

const FileTile: React.FC<{ progress: number }> = ({ progress }) => (
  <div style={{ background: COLORS.ink900, borderRadius: 12, padding: 18, color: COLORS.creme }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 14 }}>
      <span style={{ width: 22, height: 22, borderRadius: 4, background: 'rgba(245,239,227,0.16)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
        <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke={COLORS.cremeMute} strokeWidth={1.8}><path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" /><polyline points="14 3 14 9 20 9" /></svg>
      </span>
      live_set.wav
    </div>
    <div style={{ marginTop: 16, height: 8, borderRadius: 999, background: 'rgba(245,239,227,0.12)', overflow: 'hidden' }}>
      <div style={{ width: `${progress * 100}%`, height: '100%', background: COLORS.orange }} />
    </div>
    <div style={{ marginTop: 10, fontSize: 11, color: COLORS.cremeMute, fontFeatureSettings: '"tnum" 1' }}>
      Detected · {Math.round(progress * 100)}%
    </div>
  </div>
);

const ProcessTile: React.FC<{ progress: number; t: number }> = ({ progress, t }) => {
  const steps = ['Cut', 'Brand', 'Caption'];
  return (
    <div style={{ background: COLORS.ink900, borderRadius: 12, padding: 18, color: COLORS.creme }}>
      {/* three processing rows that fill in sequence */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {steps.map((s, i) => {
          const a = Math.max(0, Math.min(1, progress * 3 - i));
          return (
            <div key={s} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <span style={{ width: 14, height: 14, borderRadius: 7, border: `2px solid ${a >= 1 ? COLORS.orange : 'rgba(245,239,227,0.3)'}`, background: a >= 1 ? COLORS.orange : 'transparent', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                {a >= 1 && <svg viewBox="0 0 24 24" width="8" height="8" fill="none" stroke={COLORS.ink} strokeWidth={4}><polyline points="20 6 9 17 4 12" /></svg>}
              </span>
              <span style={{ flex: 1, height: 6, borderRadius: 3, background: 'rgba(245,239,227,0.10)', overflow: 'hidden' }}>
                <span style={{ display: 'block', width: `${a * 100}%`, height: '100%', background: 'rgba(245,239,227,0.4)' }} />
              </span>
              <span style={{ fontSize: 10, color: COLORS.cremeMute, width: 46 }}>{s}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

const PostsTile: React.FC<{ frame: number; fps: number }> = ({ frame, fps }) => {
  const platforms = [
    { name: 'TikTok' },
    { name: 'Instagram' },
    { name: 'YouTube' }
  ];
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      {platforms.map((p, i) => {
        const startF = (6.0 + i * 0.35) * fps;
        const pop = spring({ frame: frame - startF, fps, config: { damping: 14, mass: 0.6 }, durationInFrames: 26 });
        const a = Math.max(0, Math.min(1, pop));
        return (
          <div key={p.name} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: 12, borderRadius: 10, background: COLORS.ink900, color: COLORS.creme, opacity: a, transform: `translateY(${(1 - a) * 8}px)` }}>
            <span style={{ width: 22, height: 22, borderRadius: 6, background: 'rgba(245,239,227,0.14)' }} />
            <div style={{ flex: 1, fontSize: 12 }}>
              <div style={{ fontWeight: 500 }}>{p.name}</div>
              <div style={{ color: COLORS.cremeMute, fontSize: 10 }}>Scheduled</div>
            </div>
            <span style={{ width: 6, height: 6, borderRadius: 3, background: COLORS.orange }} />
          </div>
        );
      })}
    </div>
  );
};
