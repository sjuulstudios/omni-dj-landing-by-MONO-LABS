'use client';

import React from 'react';

type Props = {
  size?: number;
  spin?: boolean;
  variant?: 'creme' | 'ink';
  className?: string;
};

/**
 * The 8-circle Omni DJ ring mark. SVG version authored from the PNG reference.
 * - 8 evenly spaced circles around a central void
 * - The whole ring rotates; individual circles do not spin (their fill stays oriented)
 */
export default function OmniMark({ size = 64, spin = false, variant = 'creme', className }: Props) {
  const fill = variant === 'creme' ? '#F5EFE3' : '#0A0A0A';

  // 8 circles on a ring of radius R, each circle has radius r
  const R = 38;
  const r = 9;

  const circles = Array.from({ length: 8 }, (_, i) => {
    const angle = (i / 8) * Math.PI * 2 - Math.PI / 2; // start at top
    const cx = 50 + Math.cos(angle) * R;
    const cy = 50 + Math.sin(angle) * R;
    return <circle key={i} cx={cx} cy={cy} r={r} fill={fill} />;
  });

  return (
    <span
      className={`omni-mark ${spin ? '' : ''} ${className ?? ''}`}
      style={{ width: size, height: size }}
      aria-hidden="true"
    >
      <svg
        viewBox="0 0 100 100"
        xmlns="http://www.w3.org/2000/svg"
        className={spin ? 'omni-mark-spin' : ''}
      >
        {circles}
      </svg>
    </span>
  );
}
