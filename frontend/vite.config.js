import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    historyApiFallback: true,  // Enable SPA fallback for dev server
  },
  preview: {
    historyApiFallback: true,  // Enable SPA fallback for preview mode
  },
  build: {
    rollupOptions: {
      input: {
        main: '/index.html',
      },
    },
  },
})
