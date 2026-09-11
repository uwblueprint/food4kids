import { afterEach, describe, expect, it, vi } from 'vitest';

/**
 * Where requests go. The module reads import.meta.env at import time, so each
 * case stubs the environment and re-imports a fresh copy.
 */
async function load() {
  vi.resetModules();
  return import('@/lib/axiosClient');
}

afterEach(() => {
  vi.unstubAllEnvs();
});

describe('API base URL', () => {
  it('points a dev build at the backend container', async () => {
    vi.stubEnv('DEV', true);
    vi.stubEnv('VITE_API_BASE_URL', undefined);
    const { API_BASE_URL, default: client } = await load();
    expect(API_BASE_URL).toBe('http://localhost:8080');
    expect(client.defaults.baseURL).toBe('http://localhost:8080');
  });

  it('keeps a production build same-origin, where Hosting rewrites /api', async () => {
    vi.stubEnv('DEV', false);
    vi.stubEnv('VITE_API_BASE_URL', undefined);
    const { API_BASE_URL, default: client } = await load();
    expect(API_BASE_URL).toBe('');
    expect(client.defaults.baseURL).toBe('');
  });

  it.each([true, false])(
    'lets VITE_API_BASE_URL override either default (DEV=%s)',
    async (dev) => {
      vi.stubEnv('DEV', dev);
      vi.stubEnv('VITE_API_BASE_URL', 'https://preview.example');
      const { API_BASE_URL } = await load();
      expect(API_BASE_URL).toBe('https://preview.example');
    }
  );

  it('sends the refresh to a same-origin /api path in production', async () => {
    vi.stubEnv('DEV', false);
    vi.stubEnv('VITE_API_BASE_URL', undefined);
    const { default: client } = await load();
    const url = client.getUri({ url: '/api/auth/refresh' });
    expect(url).toBe('/api/auth/refresh');
  });
});
