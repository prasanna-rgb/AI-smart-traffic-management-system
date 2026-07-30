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
          900: '#0b0f19',
          800: '#111827',
          700: '#1f293d',
          600: '#2d3b55'
        },
        cyan: {
          400: '#38bdf8',
          500: '#06b6d4',
          600: '#0891b2'
        },
        emerald: {
          400: '#34d399',
          500: '#10b981'
        }
      }
    },
  },
  plugins: [],
}
