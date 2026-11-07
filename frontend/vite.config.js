import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Vite : remplace Create React App / react-scripts
// - dev server : npm run dev (port 3000)
// - build prod : npm run build  (genere le dossier dist/)
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    open: true,
    host: '127.0.0.1',
  },
  build: {
    outDir: 'dist',
  },
})
