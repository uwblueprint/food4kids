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
    // Node 20+ supplies File/FormData/Blob, so the request-shape tests need no
    // DOM and this stays the cheap default. Component tests opt in per file
    // with a `// @vitest-environment jsdom` docblock.
    //
    // jsdom is held at v26: from v27 it pulls html-encoding-sniffer 6, which
    // `require()`s an ES module. CI pins Node 20.11.1 (lint.yml), and
    // require(esm) only landed in 20.19 -- so a newer jsdom passes locally on
    // Node 24 and dies in CI. Raise CI's Node before raising jsdom.
    environment: 'node',
    include: ['src/**/*.test.{ts,tsx}'],
  }
})
