import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

// Separate from frontend/ on purpose: a Mini App needs to load fast on mobile networks
// inside Telegram's webview, so it stays a small, standalone bundle instead of pulling in
// the full admin site's router/sidebar/chart stack.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5174,
    // Telegram opens the app over HTTPS (via a tunnel in dev — see README.md); allow any
    // host so that tunnel's hostname isn't rejected by Vite's dev-server host check.
    allowedHosts: true,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
})
