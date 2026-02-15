// tailwind.config.js
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'neural-primary': '#6366f1',
        'neural-secondary': '#8b5cf6',
      }
    },
  },
  plugins: [],
}