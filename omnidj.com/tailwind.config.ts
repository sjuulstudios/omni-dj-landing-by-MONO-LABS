import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './lib/**/*.{js,ts,jsx,tsx,mdx}'
  ],
  theme: {
    extend: {
      colors: {
        ink: {
          DEFAULT: '#000000',
          900: '#0A0A0A',
          800: '#141414',
          700: '#1F1F1F',
          600: '#2A2A2A'
        },
        creme: {
          DEFAULT: '#F5EFE3',
          dim: '#E8DFC9',
          mute: 'rgba(245,239,227,0.72)',
          faint: 'rgba(245,239,227,0.32)',
          line: 'rgba(245,239,227,0.12)'
        },
        orange: {
          DEFAULT: '#FF6A1A',
          hover: '#FF5500',
          dim: 'rgba(255,106,26,0.18)'
        }
      },
      fontFamily: {
        sans: ['"Helvetica Neue"', 'Helvetica', 'Arial', 'sans-serif'],
        mono: ['var(--font-geist-mono)', '"SF Mono"', '"JetBrains Mono"', 'ui-monospace', 'Menlo', 'Consolas', 'monospace']
      },
      fontSize: {
        'hero': ['88px', { lineHeight: '1.0', letterSpacing: '-0.03em', fontWeight: '700' }],
        'section': ['64px', { lineHeight: '1.05', letterSpacing: '-0.025em', fontWeight: '700' }],
        'h3': ['32px', { lineHeight: '1.2', fontWeight: '500' }],
        'body-lg': ['20px', { lineHeight: '1.5', fontWeight: '300' }],
        'body': ['17px', { lineHeight: '1.55', fontWeight: '300' }],
        'caption': ['12px', { lineHeight: '1.4', letterSpacing: '0.08em', fontWeight: '500' }]
      },
      maxWidth: {
        page: '1280px',
        wide: '1440px',
        narrow: '960px'
      },
      transitionTimingFunction: {
        'smooth': 'cubic-bezier(0.16, 1, 0.3, 1)',
        'drop': 'cubic-bezier(0.16, 1, 0.3, 1)',
        'overshoot': 'cubic-bezier(0.34, 1.56, 0.64, 1)'
      },
      keyframes: {
        'spin-slow': {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' }
        },
        'fade-up': {
          '0%': { opacity: '0', transform: 'translateY(24px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' }
        },
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' }
        }
      },
      animation: {
        'spin-slow': 'spin-slow 10s linear infinite',
        'fade-up': 'fade-up 700ms cubic-bezier(0.22, 1, 0.36, 1) forwards',
        'fade-in': 'fade-in 500ms ease-out forwards'
      }
    }
  },
  plugins: []
};

export default config;
