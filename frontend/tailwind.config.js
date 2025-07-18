/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        },
        essence: {
          high: '#10b981',
          medium: '#3b82f6',
          low: '#f59e0b',
          zero: '#6b7280',
        }
      }
    },
  },
  plugins: [],
}