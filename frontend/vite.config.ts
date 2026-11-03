import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Built assets are served by the Python app (`tracepost serve`); no Node server at runtime.
export default defineConfig({
  plugins: [react()],
  build: { outDir: '../src/tracepost/static', emptyOutDir: true },
  server: { proxy: { '/api': 'http://127.0.0.1:8765' } },
})
