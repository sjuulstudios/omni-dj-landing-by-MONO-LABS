'use client';

import React, { useEffect, useRef, useState } from 'react';

type Props = {
  children: React.ReactNode;
  delay?: number;
  className?: string;
  as?: keyof JSX.IntrinsicElements;
};

/**
 * Lightweight scroll-triggered fade-up. Uses IntersectionObserver, no framer-motion dep.
 * Adds `in` class once the element enters the viewport once.
 *
 * Safety: if the element is already in viewport at mount (above-the-fold content),
 * we mark it as shown synchronously on the first effect tick so the page never
 * stalls at opacity 0 even if the observer fails to fire.
 */
export default function Reveal({ children, delay = 0, className, as: As = 'div' }: Props) {
  const ref = useRef<HTMLElement | null>(null);
  const [shown, setShown] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    // If already in viewport at mount, reveal immediately
    const rect = el.getBoundingClientRect();
    const inView = rect.top < window.innerHeight && rect.bottom > 0;
    if (inView) {
      setShown(true);
      return;
    }

    const io = new IntersectionObserver(
      entries => {
        for (const e of entries) {
          if (e.isIntersecting) {
            setShown(true);
            io.disconnect();
          }
        }
      },
      { rootMargin: '0px 0px -10% 0px', threshold: 0.05 }
    );
    io.observe(el);

    // Hard fallback: after 2s, reveal regardless. Defends against any observer hiccup.
    const fallback = window.setTimeout(() => setShown(true), 2000);

    return () => {
      io.disconnect();
      window.clearTimeout(fallback);
    };
  }, []);

  return React.createElement(
    As,
    {
      ref: ref as any,
      className: `fade-up ${shown ? 'in' : ''} ${className ?? ''}`,
      style: { transitionDelay: shown && delay > 0 ? `${delay}ms` : undefined }
    },
    children
  );
}
