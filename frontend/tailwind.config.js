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
      },
      maxWidth: {
        prose: '65ch',
      },
    },
  },
  plugins: [],
}
