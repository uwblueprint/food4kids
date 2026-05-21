import { defineConfig } from '@hey-api/openapi-ts';

export default defineConfig({
  input: './openapi.json',
  output: {
    path: 'src/api/generated',
    // Generated code is overwritten on every regen; we don't lint it.
    // Prettier still runs so diffs stay readable.
    postProcess: ['prettier'],
  },
  plugins: [
    {
      name: '@hey-api/client-axios',
      // Wires the generated client to reuse src/lib/axiosClient.ts
      // (baseURL, auth header interceptor) instead of creating its own.
      runtimeConfigPath: './src/api/runtime.ts',
    },
    '@hey-api/typescript',
    '@hey-api/sdk',
    '@tanstack/react-query',
  ],
});
