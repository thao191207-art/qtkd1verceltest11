/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          950: '#05080F',
          900: '#070C18',
          850: '#0B1220',
          800: '#0E1729',
          700: '#14213B',
          600: '#1C2C4E',
        },
        accent: {
          blue: '#2F8BFF',
          cyan: '#38BDF8',
          glow: 'rgba(47, 139, 255, 0.5)',
        },
        status: {
          green: '#34D399',
          amber: '#FBBF24',
          red: '#F87171',
          purple: '#A78BFA',
          blue: '#38BDF8',
        }
      },
      boxShadow: {
        'glass': '0 8px 32px 0 rgba(0, 0, 0, 0.45)',
        'glass-sm': '0 4px 16px 0 rgba(0, 0, 0, 0.3)',
        'glow-blue': '0 0 25px rgba(47, 139, 255, 0.5)',
        'glow-cyan': '0 0 25px rgba(56, 189, 248, 0.4)',
        'glow-card': '0 0 35px rgba(15, 23, 42, 0.8)',
      },
      borderRadius: {
        'glass': '16px',
        'glass-lg': '20px',
      }
    },
  },
  plugins: [],
}
