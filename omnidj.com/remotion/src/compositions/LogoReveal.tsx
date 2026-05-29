import React from 'react';
import { AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { COLORS } from '../colors';

/**
 * Omni DJ — Hero logo reveal
 *
 *  0.0 – 1.4s : ring fades in from the left and rotates 360°
 *  1.4 – 12s  : ring keeps a steady slow rotation
 *
 * Designed to render at 800×800 transparent-ready (still on black bg here for h264 export).
 */
export const LogoReveal: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  // Entry: 0 → 1 over the first 1.4s
  const entry = interpolate(frame, [0, 1.4 * fps], [0, 1], {
    easing: Easing.bezier(0.22, 1, 0.36, 1),
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp'
  });

  // Total rotation: 360° entry + continuous slow rotation after that (one full turn per 10s)
  const entryRot = entry * 360;
  const afterEntryFrames = Math.max(0, frame - 1.4 * fps);
  const idleRot = (afterEntryFrames / fps) * 36; // 36deg/s → 10s per rotation
  const rotation = entryRot + idleRot;

  const opacity = entry;
  const x = interpolate(entry, [0, 1], [-60, 0]);

  // 8 circles on a ring
  const R = 38;
  const r = 9.5;
  const circles = Array.from({ length: 8 }, (_, i) => {
    const angle = (i / 8) * Math.PI * 2 - Math.PI / 2;
    const cx = 50 + Math.cos(angle) * R;
    const cy = 50 + Math.sin(angle) * R;
    return <circle key={i} cx={cx} cy={cy} r={r} fill={COLORS.creme} />;
  });

  return (
    <AbsoluteFill style={{ background: COLORS.ink, alignItems: 'center', justifyContent: 'center' }}>
      <div
        style={{
          width: 640,
          height: 640,
          opacity,
          transform: `translateX(${x}px)`
        }}
      >
        <svg
          viewBox="0 0 100 100"
          xmlns="http://www.w3.org/2000/svg"
          style={{
            width: '100%',
            height: '100%',
            transform: `rotate(${rotation}deg)`,
            transformOrigin: 'center center'
          }}
        >
          {circles}
        </svg>
      </div>
    </AbsoluteFill>
  );
};
