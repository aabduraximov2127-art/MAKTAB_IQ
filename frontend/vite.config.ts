import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // `daphne` is first in INSTALLED_APPS, so `runserver` (8000) serves WebSockets too.
      // Production runs a separate daphne on 8001 behind the reverse proxy.
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
})
