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
    // Node supplies File/FormData/Blob, so the request-shape tests need no
    // DOM. Component tests opt in per file with a
    // `// @vitest-environment happy-dom` docblock, so they don't pay for it
    // here. happy-dom rather than jsdom because Radix's Select hangs under
    // user-event on jsdom 26.
    //
    // Keep frontend/Dockerfile and the CI workflows on the SAME Node (24.13.0
    // today). When they drift, a dep whose engines.node outruns CI's passes
    // every local check and fails only in CI. Verify a bump on CI's Node:
    //   docker run --rm -v "$PWD:/app" -w /app node:24.13.0 \
    //     sh -c 'corepack enable && pnpm install --frozen-lockfile && pnpm test'
    environment: 'node',
    include: ['src/**/*.test.{ts,tsx}'],
  }
})
