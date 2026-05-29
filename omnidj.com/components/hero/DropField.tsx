'use client';

import React, { useRef, useState } from 'react';

export default function DropField({ label, hint }: { label: string; hint: string }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [filename, setFilename] = useState<string | null>(null);
  const [hovering, setHovering] = useState(false);

  const onPick = () => inputRef.current?.click();

  const onChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) setFilename(f.name);
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setHovering(false);
    const f = e.dataTransfer.files?.[0];
    if (f) setFilename(f.name);
  };

  return (
    <button
      type="button"
      onClick={onPick}
      onDragOver={e => { e.preventDefault(); setHovering(true); }}
      onDragLeave={() => setHovering(false)}
      onDrop={onDrop}
      title={hint}
      className="btn w-full transition-all"
      style={{
        width: '100%',
        // Transparent secondary CTA with a dashed orange edge that solidifies on hover/drag.
        background: hovering ? 'rgba(255,106,26,0.10)' : 'transparent',
        border: `1.5px dashed ${hovering ? 'var(--orange)' : 'rgba(255,106,26,0.6)'}`,
        color: 'var(--creme)',
        transform: hovering ? 'translateY(-1px)' : 'none'
      }}
    >
      <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="var(--orange)" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M12 5v14M5 12l7-7 7 7" />
      </svg>
      <span className="font-medium">{filename ?? label}</span>
      <input
        ref={inputRef}
        type="file"
        accept=".wav,.mp3,.mp4,.aiff,.flac,.m4a"
        className="sr-only"
        onChange={onChange}
      />
    </button>
  );
}
