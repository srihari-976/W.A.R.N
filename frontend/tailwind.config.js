/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        'neon-blue': {
          50: '#e6fdff',
          100: '#ccfbff',
          200: '#99f8ff',
          300: '#66f4ff',
          400: '#33f1ff',
          500: '#00f3ff',
          600: '#00c2cc',
          700: '#009299',
          800: '#006166',
          900: '#003133',
          DEFAULT: '#00f3ff'
        },
        'neon-purple': '#b537f2',
        'neon-pink': '#ff3399',
        'cyber-black': '#0a0a0f',
        'cyber-dark': '#141419',
        'cyber-gray': '#1e1e26',
        'grid-line': 'rgba(0, 243, 255, 0.1)',
      },
      boxShadow: {
        'neon-glow': '0 0 5px #00f3ff, 0 0 20px #00f3ff',
        'neon-glow-purple': '0 0 5px #b537f2, 0 0 20px #b537f2',
        'neon-glow-pink': '0 0 5px #ff3399, 0 0 20px #ff3399',
      },
      backgroundImage: {
        'cyber-grid': 'linear-gradient(rgba(0, 243, 255, 0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(0, 243, 255, 0.1) 1px, transparent 1px)',
      },
      backgroundSize: {
        'cyber-grid': '30px 30px',
      },
      animation: {
        'pulse-neon': 'pulse-neon 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float': 'float 3s ease-in-out infinite',
      },
      keyframes: {
        'pulse-neon': {
          '0%, 100%': {
            opacity: '1',
            // Tailwind does not support textShadow natively
          },
          '50%': {
            opacity: '0.5',
          },
        },
        'float': {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
      },
    },
  },
  plugins: [],
};
