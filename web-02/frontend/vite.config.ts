import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const apiTarget = process.env.WEB02_API_TARGET || 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [react()],
  build: { rollupOptions: { output: { manualChunks: { katex: ['katex'] } } } },
  server: { port: 5173, proxy: { '/api': apiTarget } },
  preview: { port: 4173, proxy: { '/api': apiTarget } },
})
