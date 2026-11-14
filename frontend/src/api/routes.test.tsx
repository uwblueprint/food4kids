// @vitest-environment happy-dom
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, cleanup, renderHook } from '@testing-library/react';
import type { ReactNode } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import {
  getDriverHistoryQueryKey,
  getDriverHistorySummaryQueryKey,
  getDriverQueryKey,
  getDriversQueryKey,
  getRouteGroupsQueryKey,
  getRouteQueryKey,
  getRoutesQueryKey,
} from './generated/@tanstack/react-query.gen';
import { useUpdateRoute } from './routes';

vi.mock('./generated/sdk.gen', async (original) => ({
  ...(await original<object>()),
  updateRoute: () => ({ data: { route_id: 'route-1' } }),
}));

afterEach(cleanup);

describe('Route update cache refresh', () => {
  it.each([
    { body: { driver_id: 'new-driver' }, refreshDrivers: true },
    { body: { driver_id: null }, refreshDrivers: true },
    { body: { name: 'New route name' }, refreshDrivers: false },
    { body: { start_time: '10:00:00' }, refreshDrivers: false },
  ])(
    'refreshes assignment data only for a driver change: $body',
    async ({ body, refreshDrivers }) => {
      const client = new QueryClient({
        defaultOptions: { mutations: { retry: false } },
      });
      // Actual generated keys ensure the endpoint scopes match filtered lists
      // and path-specific caches for both the previous and the new driver.
      const driverKeys = [
        getDriversQueryKey({ query: { page: 2 } }),
        ...['old-driver', 'new-driver'].flatMap((driver_id) => [
          getDriverHistoryQueryKey({
            path: { driver_id },
            query: { year: 2026 },
          }),
          getDriverHistorySummaryQueryKey({ path: { driver_id } }),
        ]),
      ];
      const routeKeys = [
        getRoutesQueryKey({ query: { unassigned_only: true } }),
        getRoutesQueryKey({ query: { driver_id: 'old-driver' } }),
        getRouteGroupsQueryKey(),
        getRouteQueryKey({ path: { route_id: 'route-1' } }),
      ];
      const untouched = [
        getDriverQueryKey({ path: { driver_id: 'old-driver' } }),
        getRouteQueryKey({ path: { route_id: 'other-route' } }),
      ];
      [...driverKeys, ...routeKeys, ...untouched].forEach((key) =>
        client.setQueryData(key, {})
      );
      const { result, unmount } = renderHook(() => useUpdateRoute(), {
        wrapper: ({ children }: { children: ReactNode }) => (
          <QueryClientProvider client={client}>{children}</QueryClientProvider>
        ),
      });
      await act(async () => {
        await result.current.mutateAsync({
          path: { route_id: 'route-1' },
          body,
        });
      });
      driverKeys.forEach((key) =>
        expect(client.getQueryState(key)?.isInvalidated).toBe(refreshDrivers)
      );
      routeKeys.forEach((key) =>
        expect(client.getQueryState(key)?.isInvalidated).toBe(true)
      );
      untouched.forEach((key) =>
        expect(client.getQueryState(key)?.isInvalidated).toBe(false)
      );
      unmount();
      client.clear();
    }
  );
});
