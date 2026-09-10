// @vitest-environment happy-dom
import { cleanup, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';

import type { RouteDetailRead } from '@/api/generated/types.gen';

import { RouteDetailView } from './RouteDetailView';

/**
 * The header's subtitle names the day the driver is expected to drive. That
 * day arrives as a date-only string ("2026-08-31"), which `new Date()` reads
 * as UTC midnight — the previous evening anywhere west of Greenwich, and so a
 * day early on screen. This renders the real component on clocks either side
 * of UTC to pin the date the driver actually sees.
 */
const route: RouteDetailRead = {
  drive_date: '2026-08-31',
  length: 12.5,
  name: 'Route 4',
  route_group_id: 'group-1',
  route_id: 'route-1',
  start_time: '08:00:00',
  stops: [],
};

vi.mock('@/common/hooks/useRoute', () => ({
  useRoute: () => ({ data: route, isLoading: false, isError: false }),
}));

vi.mock('@/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/api')>()),
  useOrgContact: () => ({ data: undefined }),
}));

// Leaflet wants a real layout box; the map is not what these assert on.
vi.mock('@/common/components/RouteMap', () => ({
  RouteMap: () => <div data-testid="route-map" />,
}));

const HOST_TIMEZONE = process.env.TZ;

afterEach(() => {
  process.env.TZ = HOST_TIMEZONE;
  cleanup();
});

const renderIn = (zone: string) => {
  process.env.TZ = zone;
  render(
    <MemoryRouter>
      <RouteDetailView routeId="route-1" />
    </MemoryRouter>
  );
};

describe('RouteDetailView', () => {
  // Spans the offset range: UTC-11 through UTC+14. Only the negative offsets
  // can catch the UTC-midnight bug, but a host in a positive one would
  // otherwise pass a broken implementation without noticing.
  it.each([
    'Pacific/Niue', // UTC-11
    'Pacific/Honolulu', // UTC-10
    'America/Los_Angeles', // UTC-7 in August
    'America/Toronto', // UTC-4 in August — where the deliveries happen
    'UTC',
    'Europe/Berlin', // UTC+2 in August
    'Asia/Tokyo', // UTC+9
    'Pacific/Kiritimati', // UTC+14
  ])('shows the drive date the backend sent, on a clock in %s', (zone) => {
    renderIn(zone);

    expect(screen.getByText(/Aug 31/)).toBeTruthy();
    expect(screen.queryByText(/Aug 30/)).toBeNull();
  });

  it('renders the rest of the subtitle beside the date', () => {
    renderIn('America/Toronto');

    expect(screen.getByText(/8:00 AM/)).toBeTruthy();
    expect(screen.getByRole('heading', { name: 'Route 4' })).toBeTruthy();
  });
});
