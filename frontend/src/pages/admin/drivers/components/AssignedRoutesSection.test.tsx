// @vitest-environment happy-dom
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import type {
  GetRoutesData,
  RouteWithDateRead,
  UpdateRouteData,
} from '@/api/generated/types.gen';

import { AssignedRoutesSection } from './AssignedRoutesSection';

function route(
  id: string,
  driverId: string | null,
  startTime: string | null = '08:45:00'
): RouteWithDateRead {
  return {
    route_id: id,
    name: `Route ${id}`,
    driver_id: driverId,
    driver_name: driverId ? 'Alex Morgan' : null,
    drive_date: '2026-11-09',
    route_group_id: 'group-1',
    group_name: 'Monday schools',
    num_stops: 8,
    length: 10,
    box_total: 4,
    notes: '',
    start_time: startTime,
    status: 'Upcoming',
  };
}
let routes: RouteWithDateRead[];
let failPatch = false;
let failList = false;
let releasePatch: (() => void) | undefined;
let pendingPatch: Promise<void> | undefined;
const listRequests = vi.fn();
const patchRequests = vi.fn();
const clients: QueryClient[] = [];
vi.mock('@/api/generated/sdk.gen', async (original) => ({
  ...(await original<object>()),
  getRoutes: ({ query }: { query: NonNullable<GetRoutesData['query']> }) => {
    listRequests(query);
    if (failList) throw new Error('Unavailable');
    let items = routes.filter((r) =>
      query.unassigned_only
        ? r.driver_id === null
        : r.driver_id === query.driver_id
    );
    if (query.search)
      items = items.filter((r) =>
        r.name.toLowerCase().includes(query.search!.toLowerCase())
      );
    const page = query.page ?? 1;
    const size = query.page_size ?? 20;
    return {
      data: {
        items: items.slice((page - 1) * size, page * size),
        total: items.length,
        page,
        page_size: size,
        total_pages: Math.ceil(items.length / size),
      },
    };
  },
  updateRoute: async (options: UpdateRouteData) => {
    patchRequests(options);
    if (pendingPatch) await pendingPatch;
    if (failPatch) throw new Error('Assignment failed');
    const existing = routes.find((r) => r.route_id === options.path.route_id)!;
    Object.assign(existing, options.body);
    return { data: { ...existing } };
  },
  getDrivers: () => ({
    data: {
      items: [
        { driver_id: 'driver-2', first_name: 'Blair', last_name: 'Smith' },
      ],
    },
  }),
  getSuggestedDriver: () => ({ data: null }),
}));
beforeEach(() => {
  routes = [route('assigned', 'driver-1'), route('unassigned', null, null)];
  failPatch = false;
  failList = false;
  pendingPatch = undefined;
  releasePatch = undefined;
  listRequests.mockClear();
  patchRequests.mockClear();
});
afterEach(() => {
  cleanup();
  clients.forEach((c) => c.clear());
  clients.length = 0;
});
function renderSection() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  clients.push(client);
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <AssignedRoutesSection driverId="driver-1" driverName="Alex Morgan" />
      </MemoryRouter>
    </QueryClientProvider>
  );
}
async function editRoute() {
  fireEvent.click(await screen.findByRole('button', { name: 'Edit' }));
  expect(screen.getByText('Select a route to edit')).toBeDefined();
  fireEvent.click(screen.getByRole('button', { name: /Route assigned/ }));
}
async function openAssign() {
  fireEvent.click(await screen.findByRole('button', { name: 'Assign' }));
  return screen.findByRole('dialog', { name: 'Assign Route' });
}
describe('Driver sidebar route actions', () => {
  it('does not submit a selected route that disappears from the unassigned feed', async () => {
    renderSection();
    const dialog = await openAssign();
    fireEvent.click(
      await within(dialog).findByRole('radio', { name: /Route unassigned/ })
    );
    routes = routes.filter((item) => item.route_id !== 'unassigned');
    await clients[0].invalidateQueries();
    expect(
      await within(dialog).findByText('No unassigned routes available.')
    ).toBeDefined();
    expect(
      within(dialog)
        .getByRole('button', { name: 'Assign' })
        .matches(':disabled')
    ).toBe(true);
    expect(patchRequests).not.toHaveBeenCalled();
  });

  it('allows a custom start time when assigning a route', async () => {
    renderSection();
    const dialog = await openAssign();
    fireEvent.click(
      await within(dialog).findByRole('radio', { name: /Route unassigned/ })
    );
    const time = within(dialog).getByRole('textbox', { name: 'Time' });
    fireEvent.change(time, { target: { value: '10:15 AM' } });
    fireEvent.blur(time);
    fireEvent.click(within(dialog).getByRole('button', { name: 'Assign' }));
    await waitFor(() =>
      expect(patchRequests).toHaveBeenCalledWith(
        expect.objectContaining({
          body: { driver_id: 'driver-1', start_time: '10:15:00' },
        })
      )
    );
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
  });

  it('unassigns from edit mode and refreshes the sidebar', async () => {
    renderSection();
    expect(
      (
        await screen.findByRole('link', { name: /Route assigned/ })
      ).getAttribute('href')
    ).toBe('/admin/routes/assigned');
    await editRoute();
    fireEvent.click(screen.getByRole('button', { name: 'Unassign' }));
    await waitFor(() =>
      expect(patchRequests).toHaveBeenCalledWith(
        expect.objectContaining({
          path: { route_id: 'assigned' },
          body: { driver_id: null },
        })
      )
    );
    expect(await screen.findByText('No Assigned Routes')).toBeDefined();
    fireEvent.click(screen.getByRole('button', { name: 'Done' }));
    expect(screen.queryByText('Select a route to edit')).toBeNull();
  });
  it('reuses the reassignment modal and preserves start time', async () => {
    renderSection();
    await editRoute();
    fireEvent.click(screen.getByRole('button', { name: 'Reassign' }));
    const dialog = await screen.findByRole('dialog', {
      name: 'Reassign Driver',
    });
    expect(within(dialog).getByText('Alex Morgan')).toBeDefined();
    fireEvent.keyDown(within(dialog).getByRole('combobox'), {
      key: 'ArrowDown',
    });
    fireEvent.click(await screen.findByRole('option', { name: 'Blair Smith' }));
    fireEvent.click(within(dialog).getByRole('button', { name: 'Reassign' }));
    await waitFor(() =>
      expect(patchRequests).toHaveBeenCalledWith(
        expect.objectContaining({
          path: { route_id: 'assigned' },
          body: { driver_id: 'driver-2', start_time: '08:45:00' },
        })
      )
    );
    expect(await screen.findByText('No Assigned Routes')).toBeDefined();
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
  });
  it('assigns only an unassigned route to the selected driver, supplying the required default start time', async () => {
    renderSection();
    const dialog = await openAssign();
    const radio = await within(dialog).findByRole('radio', {
      name: /Route unassigned/,
    });
    expect(
      within(dialog).queryByRole('radio', { name: /Route assigned/ })
    ).toBeNull();
    expect(
      within(dialog)
        .getByRole('button', { name: 'Assign' })
        .matches(':disabled')
    ).toBe(true);
    fireEvent.click(radio);
    fireEvent.click(within(dialog).getByRole('button', { name: 'Assign' }));
    await waitFor(() =>
      expect(patchRequests).toHaveBeenCalledWith(
        expect.objectContaining({
          path: { route_id: 'unassigned' },
          body: { driver_id: 'driver-1', start_time: '09:00:00' },
        })
      )
    );
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
    expect(
      await screen.findByRole('link', { name: /Route unassigned/ })
    ).toBeDefined();
  });
  it('supports assigning with no existing assignments, empty results, and load-error retry', async () => {
    routes = [];
    renderSection();
    await screen.findByText('No Assigned Routes');
    const dialog = await openAssign();
    expect(
      await within(dialog).findByText('No unassigned routes available.')
    ).toBeDefined();
    fireEvent.click(within(dialog).getByRole('button', { name: 'Cancel' }));
    failList = true;
    const reopened = await openAssign();
    expect(
      await within(reopened).findByText("Couldn't load unassigned routes.")
    ).toBeDefined();
    failList = false;
    routes = [route('new', null)];
    fireEvent.click(within(reopened).getByRole('button', { name: 'Retry' }));
    expect(
      await within(reopened).findByRole('radio', { name: /Route new/ })
    ).toBeDefined();
    expect(patchRequests).not.toHaveBeenCalled();
  });
  it('paginates all unassigned routes, searches on the server, and clears selection on navigation and reopen', async () => {
    routes = Array.from({ length: 21 }, (_, i) => route(`demo-${i + 1}`, null));
    renderSection();
    const dialog = await openAssign();
    fireEvent.click(
      await within(dialog).findByRole('radio', { name: /Route demo-1 Monday/ })
    );
    fireEvent.click(within(dialog).getByRole('button', { name: 'Page 2' }));
    const last = await within(dialog).findByRole('radio', {
      name: /Route demo-21/,
    });
    expect(
      within(dialog)
        .getByRole('button', { name: 'Assign' })
        .matches(':disabled')
    ).toBe(true);
    fireEvent.click(last);
    fireEvent.change(
      within(dialog).getByRole('textbox', { name: 'Search routes' }),
      { target: { value: 'absent' } }
    );
    expect(
      await within(dialog).findByText('No results. Try being less specific.')
    ).toBeDefined();
    expect(listRequests).toHaveBeenCalledWith(
      expect.objectContaining({
        unassigned_only: true,
        page: 1,
        search: 'absent',
      })
    );
    fireEvent.click(within(dialog).getByRole('button', { name: 'Cancel' }));
    const reopened = await openAssign();
    await within(reopened).findByRole('radio', { name: /Route demo-1 Monday/ });
    expect(
      (
        within(reopened).getByRole('textbox', {
          name: 'Search routes',
        }) as HTMLInputElement
      ).value
    ).toBe('');
    expect(
      within(reopened)
        .getByRole('button', { name: 'Assign' })
        .matches(':disabled')
    ).toBe(true);
    expect(patchRequests).not.toHaveBeenCalled();
  });
  it('keeps assignment failures retryable and prevents duplicate submission', async () => {
    renderSection();
    const dialog = await openAssign();
    fireEvent.click(
      await within(dialog).findByRole('radio', { name: /Route unassigned/ })
    );
    failPatch = true;
    fireEvent.click(within(dialog).getByRole('button', { name: 'Assign' }));
    expect(await within(dialog).findByRole('alert')).toBeDefined();
    failPatch = false;
    pendingPatch = new Promise<void>((resolve) => {
      releasePatch = resolve;
    });
    fireEvent.click(within(dialog).getByRole('button', { name: 'Assign' }));
    await waitFor(() =>
      expect(
        within(dialog)
          .getByRole('button', { name: 'Assigning…' })
          .matches(':disabled')
      ).toBe(true)
    );
    expect(
      within(dialog)
        .getByRole('button', { name: 'Cancel' })
        .matches(':disabled')
    ).toBe(true);
    releasePatch!();
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
    expect(patchRequests).toHaveBeenCalledTimes(2);
  });
  it('retains the assigned route when unassign fails, allowing retry', async () => {
    renderSection();
    await editRoute();
    failPatch = true;
    fireEvent.click(screen.getByRole('button', { name: 'Unassign' }));
    expect(
      await screen.findByText("Couldn't unassign this route. Please try again.")
    ).toBeDefined();
    expect(
      screen.getByRole('button', { name: /Route assigned/ })
    ).toBeDefined();
    failPatch = false;
    fireEvent.click(screen.getByRole('button', { name: 'Unassign' }));
    expect(await screen.findByText('No Assigned Routes')).toBeDefined();
  });
});
