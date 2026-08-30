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
    // DOM. Component tests opt in per file with a
    // `// @vitest-environment happy-dom` docblock, so they don't pay for it
    // here. happy-dom rather than jsdom because Radix's Select hangs under
    // user-event on jsdom 26 — and 26/27 are the newest jsdom that CI's Node
    // 20.11.1 can run, since jsdom 28 pulls html-encoding-sniffer@6, which
    // require()s an ES module and so needs the support added in Node 20.19.
    environment: 'node',
    include: ['src/**/*.test.{ts,tsx}'],
  }
})
