// vite.config.ts
// FIXED ENV-01: hmr.host ya no es IP hardcodeada.
// Usa localhost por defecto; sobreescribible con VITE_HMR_HOST env var.
// Ejemplo para acceso LAN: VITE_HMR_HOST=192.168.1.40 npm run dev
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',       // Escuchar en todas las interfaces de red
    port: 5173,
    strictPort: true,
    hmr: {
      // FIXED: era '192.168.1.40' (hardcodeado). Ahora dinámico.
      // localhost funciona en WSL2 desde el mismo host; para acceso LAN usa env var.
      host: process.env.VITE_HMR_HOST || 'localhost',
      port: 5173
    },
    cors: true,
    watch: {
      usePolling: true
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true
  }
})