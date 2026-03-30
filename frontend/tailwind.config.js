/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        page: '#FAFAF8',
        surface: '#FEFEFE',
        primary: '#1A1917',
        secondary: '#6B6860',
        muted: '#9C9789',
        accent: {
          DEFAULT: '#0D7377',
          hover: '#0A5F62',
          light: '#E8F4F4',
        },
        warm: {
          50: '#FAF9F7',
          100: '#F3F1ED',
          200: '#E8E5E0',
          300: '#D4D0C8',
          400: '#B0ACA3',
          500: '#8C8880',
          600: '#6B6860',
          700: '#4A4843',
          800: '#2E2D2A',
          900: '#1A1917',
        },
        border: '#E0DDD7',
        'border-light': '#EAE8E3',
        score: {
          good: '#3D8B5E',
          medium: '#C08832',
          bad: '#C25544',
        },
      },
      fontFamily: {
        display: ['"Instrument Sans"', 'system-ui', 'sans-serif'],
        body: ['Figtree', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', '"Fira Code"', '"Cascadia Code"', 'ui-monospace', 'monospace'],
      },
      maxWidth: {
        prose: '65ch',
      },
      keyframes: {
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        'slide-up': {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'scale-in': {
          '0%': { opacity: '0', transform: 'scale(0.88)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        'count-up': {
          '0%': { opacity: '0', transform: 'translateY(6px) scale(0.95)' },
          '60%': { opacity: '1' },
          '100%': { opacity: '1', transform: 'translateY(0) scale(1)' },
        },
        'pulse-subtle': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.55' },
        },
      },
      animation: {
        'fade-in': 'fade-in 400ms ease-out both',
        'fade-in-slow': 'fade-in 700ms ease-out both',
        'slide-up': 'slide-up 450ms cubic-bezier(0.25, 0.46, 0.45, 0.94) both',
        'slide-up-slow': 'slide-up 650ms cubic-bezier(0.25, 0.46, 0.45, 0.94) both',
        'scale-in': 'scale-in 350ms cubic-bezier(0.34, 1.2, 0.64, 1) both',
        'count-up': 'count-up 500ms cubic-bezier(0.25, 0.46, 0.45, 0.94) both',
        'pulse-subtle': 'pulse-subtle 2800ms ease-in-out infinite',
      },
    },
  },
  plugins: [],
}
