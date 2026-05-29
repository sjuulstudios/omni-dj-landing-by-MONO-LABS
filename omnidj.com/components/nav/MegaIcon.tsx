import React from 'react';

const common = {
  width: 18,
  height: 18,
  viewBox: '0 0 24 24',
  fill: 'none' as const,
  stroke: 'currentColor',
  strokeWidth: 1.6,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const
};

export default function MegaIcon({ kind }: { kind?: string }) {
  switch (kind) {
    case 'wave':
      return <svg {...common}><path d="M3 12h2l2-7 3 14 3-10 2 7 2-5 2 3h2" /></svg>;
    case 'scissors':
      return <svg {...common}><circle cx="6" cy="6" r="3" /><circle cx="6" cy="18" r="3" /><path d="M20 4 8.12 15.88" /><path d="M14.47 14.48 20 20" /><path d="M8.12 8.12 12 12" /></svg>;
    case 'camera':
      return <svg {...common}><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" /><circle cx="12" cy="13" r="4" /></svg>;
    case 'palette':
      return <svg {...common}><circle cx="13.5" cy="6.5" r=".5" fill="currentColor" /><circle cx="17.5" cy="10.5" r=".5" fill="currentColor" /><circle cx="8.5" cy="7.5" r=".5" fill="currentColor" /><circle cx="6.5" cy="12.5" r=".5" fill="currentColor" /><path d="M12 2a10 10 0 0 0 0 20 4 4 0 0 0 4-4 2 2 0 0 1 2-2h2a4 4 0 0 0 4-4 10 10 0 0 0-12-10z" /></svg>;
    case 'caption':
      return <svg {...common}><rect x="3" y="5" width="18" height="14" rx="2" /><path d="M7 14h2M11 14h6M7 10h10" /></svg>;
    case 'target':
      return <svg {...common}><circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="5" /><circle cx="12" cy="12" r="1.5" fill="currentColor" /></svg>;
    case 'rail':
      return <svg {...common}><rect x="3" y="4" width="6" height="16" rx="1" /><rect x="11" y="6" width="6" height="12" rx="1" /><rect x="19" y="9" width="2.5" height="6" rx="0.5" /></svg>;
    case 'share':
      return <svg {...common}><circle cx="18" cy="5" r="3" /><circle cx="6" cy="12" r="3" /><circle cx="18" cy="19" r="3" /><path d="M8.6 13.5l6.8 4M15.4 6.5l-6.8 4" /></svg>;
    case 'calendar':
      return <svg {...common}><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4" /></svg>;
    case 'chart':
      return <svg {...common}><path d="M3 20h18" /><path d="M6 16v-4M11 16V8M16 16v-6M21 16V6" /></svg>;
    case 'dj':
      return <svg {...common}><circle cx="7" cy="12" r="4" /><circle cx="17" cy="12" r="4" /><path d="M7 12v.01M17 12v.01" /></svg>;
    case 'film':
      return <svg {...common}><rect x="3" y="3" width="18" height="18" rx="2" /><path d="M7 3v18M17 3v18M3 12h18M3 7h4M3 17h4M17 7h4M17 17h4" /></svg>;
    case 'users':
      return <svg {...common}><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" /></svg>;
    case 'event':
      return <svg {...common}><path d="M3 21h18" /><path d="M5 21V8l7-5 7 5v13" /><path d="M10 21v-7h4v7" /></svg>;
    case 'flag':
      return <svg {...common}><path d="M4 22V4" /><path d="M4 4h12l-2 4 2 4H4" /></svg>;
    case 'disc':
      return <svg {...common}><circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="3" /><path d="M12 9v.01" /></svg>;
    default:
      return <svg {...common}><circle cx="12" cy="12" r="4" /></svg>;
  }
}
