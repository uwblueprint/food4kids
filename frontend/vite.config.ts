import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true, // Allow external connections (for Docker)
    watch: {
      usePolling: true, // Enable polling for file changes in Docker
      interval: 1000, // Poll every 1 second
    },
    proxy: {
      // Proxy API requests to the backend
      '/api': {
        target: 'http://backend:8080',
        changeOrigin: true,
        secure: false,
      },
    },
  },
  build: {
    outDir: 'build',
    sourcemap: true,
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  define: {
    // Define global constants
    global: 'globalThis',
  },
})
