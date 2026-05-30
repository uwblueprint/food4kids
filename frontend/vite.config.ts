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
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      '@tanstack/react-query',
      '@tanstack/react-query-devtools',
      'radix-ui',
      'lucide-react',
      'date-fns',
      'clsx',
      'tailwind-merge',
    ],
  },
  server: {
    port: 3000,
    host: true, // Important for Docker
  }
})
