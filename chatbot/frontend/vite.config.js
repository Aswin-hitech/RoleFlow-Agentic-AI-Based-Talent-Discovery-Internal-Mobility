import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// The /api proxy keeps the browser same-origin, so no CORS setup is needed.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
      },
    },
  },
})
