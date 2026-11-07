import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// La API corre en 8000; Vite la proxya para que la web funcione en local y por
// Tailscale sin exponer CORS ni URLs absolutas en el navegador.
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
