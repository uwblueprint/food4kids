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
    // DOM, and node is much cheaper to start. Component tests opt into jsdom
    // per file with a `// @vitest-environment jsdom` docblock — see
    // src/App.roleGuards.test.tsx.
    //
    // KEEP jsdom BELOW 28 until CI's Node moves. CI pins Node 20.11.1
    // (.github/workflows/lint.yml) — OLDER than this app's own Dockerfile
    // (node:24.13.0) and almost certainly older than your machine. That gap is
    // the trap: jsdom >= 28 depends on html-encoding-sniffer@6, which
    // `require()`s @exodus/bytes, an ESM-only package. require(esm) landed in
    // Node 20.19, so those versions declare
    // `engines.node: ^20.19.0 || ^22.12.0 || >=24.0.0` and blow up on 20.11.1
    // with ERR_REQUIRE_ESM — in the jsdom test files only, after every local
    // check has passed. (jsdom 27 is still on html-encoding-sniffer@4 and is
    // fine; 28 is where it breaks.) Verify any bump on CI's Node, not yours:
    //   docker run --rm -v "$PWD:/app" -w /app node:20.11.1 \
    //     sh -c 'corepack enable && pnpm install --frozen-lockfile && pnpm test'
    environment: 'node',
    include: ['src/**/*.test.{ts,tsx}'],
  }
})
