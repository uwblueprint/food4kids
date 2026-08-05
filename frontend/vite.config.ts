/// <reference types="vitest/config" />
import react from '@vitejs/plugin-react'
import path from 'path'
import { defineConfig } from 'vite'
import svgr from 'vite-plugin-svgr'

// https://vite.dev/config/
export default defineConfig({
  plugins: [svgr(), react()],
  resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
  server: {
    port: 3000,
    host: true, // Important for Docker
  },
  test: {
    // Node 20+ supplies File/FormData/Blob, so these request-shape tests need
    // no DOM. Add jsdom here if we ever test components.
    environment: 'node',
    include: ['src/**/*.test.{ts,tsx}'],
  }
})
