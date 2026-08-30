// @vitest-environment happy-dom
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import type {
  DriverRead,
  RouteDetailRead,
  SuggestedDriverResponse,
} from '@/api/generated/types.gen';

import { ReassignDriverModal } from './ReassignDriverModal';

const DRIVERS = [
  { driver_id: 'd-1', first_name: 'Marcus', last_name: 'Smith' },
  { driver_id: 'd-2', first_name: 'Sarah', last_name: 'Lee' },
] as unknown as DriverRead[];

/** Set per-test; null means the API has no candidate for this route. */
let suggestion: SuggestedDriverResponse | null = null;

/**
 * Stands in for PATCH /routes/{id}, enforcing the same invariant the API does
 * (route_service.update_route, backed by the DB's
 * ck_routes_assigned_route_has_start_time): a route with a driver must have a
 * start time. Generated routes have none, so assigning without sending one is
 * exactly the 400 admins were hitting.
 */
const patchRoute = vi.fn(
  ({
    body,
  }: {
    path: { route_id: string };
    body: { driver_id?: string | null; start_time?: string | null };
  }) => {
    if (body.driver_id && !body.start_time) {
      throw new Error('An assigned route must have a start_time');
    }
    return { data: { ...body } as RouteDetailRead };
  }
);

vi.mock('@/api/generated/sdk.gen', async (importOriginal) => ({
  ...(await importOriginal<object>()),
  getDrivers: () => ({ data: DRIVERS }),
  getSuggestedDriver: () => ({ data: suggestion }),
  updateRoute: (options: Parameters<typeof patchRoute>[0]) =>
    patchRoute(options),
}));

beforeEach(() => {
  suggestion = null;
  patchRoute.mockClear();
});

// Vitest runs without `globals`, so React Testing Library cannot register its
// own auto-cleanup and rendered trees would otherwise pile up across tests.
afterEach(cleanup);

function renderModal(
  props: Partial<React.ComponentProps<typeof ReassignDriverModal>> = {}
) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <ReassignDriverModal
          open
          onOpenChange={() => {}}
          routeId="r-1"
          routeGroupId="rg-1"
          {...props}
        />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

/** Pick a driver from the Radix dropdown by its displayed name. */
async function selectDriver(user: ReturnType<typeof userEvent.setup>) {
  await user.click(screen.getByRole('combobox'));
  await user.click(await screen.findByRole('option', { name: 'Marcus Smith' }));
}

describe('ReassignDriverModal', () => {
  it('assigns an unassigned route with driver and start time in one request', async () => {
    const user = userEvent.setup();
    const onUpdated = vi.fn();
    renderModal({ onUpdated });

    expect(
      screen.getByRole('heading', { name: 'Assign Driver' })
    ).toBeDefined();

    await selectDriver(user);
    await user.click(screen.getByRole('button', { name: 'Assign' }));

    await waitFor(() => expect(onUpdated).toHaveBeenCalled());
    expect(patchRoute).toHaveBeenCalledWith(
      expect.objectContaining({
        path: { route_id: 'r-1' },
        // Both fields together — a driver_id-only PATCH is the 400.
        body: { driver_id: 'd-1', start_time: '09:00:00' },
      })
    );
    expect(screen.queryByText(/Something went wrong/)).toBeNull();
  });

  it('sends the route’s existing start time when reassigning', async () => {
    const user = userEvent.setup();
    renderModal({ currentDriverName: 'Jane Doe', startTime: '07:45:00' });

    expect(
      screen.getByRole('heading', { name: 'Reassign Driver' })
    ).toBeDefined();
    expect(screen.getByText('Jane Doe')).toBeDefined();
    expect(screen.getByText('7:45 AM')).toBeDefined();

    await selectDriver(user);
    await user.click(screen.getByRole('button', { name: 'Reassign' }));

    await waitFor(() =>
      expect(patchRoute).toHaveBeenCalledWith(
        expect.objectContaining({
          body: { driver_id: 'd-1', start_time: '07:45:00' },
        })
      )
    );
  });

  it('submits a start time picked in the time picker', async () => {
    const user = userEvent.setup();
    renderModal();

    await selectDriver(user);
    await user.click(screen.getByText('9:00 AM'));
    // 11 names only an hour — minutes are the 5s, so 10/15/… would be ambiguous.
    await user.click(await screen.findByRole('button', { name: '11' }));
    await user.click(screen.getByRole('button', { name: 'PM' }));
    await user.keyboard('{Escape}');
    await user.click(screen.getByRole('button', { name: 'Assign' }));

    await waitFor(() =>
      expect(patchRoute).toHaveBeenCalledWith(
        expect.objectContaining({
          body: { driver_id: 'd-1', start_time: '23:00:00' },
        })
      )
    );
  });

  it('shows the suggested driver as helper text when the API returns one', async () => {
    suggestion = { driver_id: 'd-2', driver_name: 'Sarah Lee' };
    renderModal();

    expect(
      await screen.findByText('Similar routes driven by Sarah Lee')
    ).toBeDefined();
  });

  it('shows no suggestion line when the API has no candidate', async () => {
    renderModal();

    // The drivers list resolving proves the queries settled, so the missing
    // suggestion is an answered "none" rather than a pending request.
    await screen.findByRole('combobox');
    await waitFor(() =>
      expect(screen.queryByText(/Similar routes driven by/)).toBeNull()
    );
  });

  it('surfaces the error when the assignment is rejected', async () => {
    const user = userEvent.setup();
    patchRoute.mockImplementationOnce(() => {
      throw new Error('boom');
    });
    renderModal();

    await selectDriver(user);
    await user.click(screen.getByRole('button', { name: 'Assign' }));

    expect(
      await screen.findByText(/Something went wrong assigning the driver/)
    ).toBeDefined();
  });

  it('links to the individual route unless the caller is already there', () => {
    const { unmount } = renderModal();
    expect(
      screen.getByRole('link', { name: 'View route' }).getAttribute('href')
    ).toBe('/admin/routes/r-1');
    unmount();

    renderModal({ showViewRoute: false });
    expect(screen.queryByRole('link', { name: 'View route' })).toBeNull();
  });
});
