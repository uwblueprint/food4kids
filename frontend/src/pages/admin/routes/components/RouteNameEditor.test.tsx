// @vitest-environment happy-dom
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import {
  getRouteGroupsQueryKey,
  getRoutesQueryKey,
} from '@/api/generated/@tanstack/react-query.gen';
import type { UpdateRouteData } from '@/api/generated/types.gen';
import { useRoute } from '@/common/hooks/useRoute';

import { RouteNameEditor } from './RouteNameEditor';

let currentName: string;
let fail = false;
let pending: Promise<void> | undefined;
let release: (() => void) | undefined;
const patch = vi.fn();
const clients: QueryClient[] = [];

vi.mock('@/api/generated/sdk.gen', async (original) => ({
  ...(await original<object>()),
  getRoute: () => ({ data: { route_id: 'route-1', name: currentName } }),
  updateRoute: async (options: UpdateRouteData) => {
    patch(options);
    if (pending) await pending;
    if (fail) throw new Error('Unavailable');
    currentName = options.body.name!;
    return { data: { route_id: 'route-1', name: currentName } };
  },
}));

beforeEach(() => {
  currentName = 'Original route';
  fail = false;
  pending = undefined;
  release = undefined;
  patch.mockClear();
});
afterEach(() => {
  cleanup();
  clients.forEach((c) => c.clear());
  clients.length = 0;
});

function RouteHeader() {
  const { data } = useRoute('route-1');
  return data ? (
    <RouteNameEditor routeId={data.route_id} name={data.name ?? ''} />
  ) : null;
}

function renderEditor() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  clients.push(client);
  client.setQueryData(getRoutesQueryKey(), {});
  client.setQueryData(getRouteGroupsQueryKey(), {});
  render(
    <QueryClientProvider client={client}>
      <RouteHeader />
    </QueryClientProvider>
  );
  return client;
}

async function openEditor() {
  const trigger = await screen.findByRole('button', {
    name: 'Edit route name',
  });
  fireEvent.click(trigger);
  return screen.findByRole('textbox', { name: /^Route name/ });
}

describe('Rename an individual admin route', () => {
  it('prefills the name, trims the edit, saves only the name, and refreshes the header and lists', async () => {
    const client = renderEditor();
    const input = await openEditor();
    expect((input as HTMLInputElement).value).toBe('Original route');
    expect(
      screen.getByRole('button', { name: 'Save' }).matches(':disabled')
    ).toBe(true);
    fireEvent.change(input, { target: { value: '  School delivery  ' } });
    fireEvent.submit(input.closest('form')!);
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
    expect(await screen.findByText('School delivery')).toBeDefined();
    expect(patch).toHaveBeenCalledWith(
      expect.objectContaining({
        path: { route_id: 'route-1' },
        body: { name: 'School delivery' },
      })
    );
    expect(client.getQueryState(getRoutesQueryKey())?.isInvalidated).toBe(true);
    expect(client.getQueryState(getRouteGroupsQueryKey())?.isInvalidated).toBe(
      true
    );
  });

  it('cancels or escapes without saving and restores the latest name on reopen', async () => {
    renderEditor();
    let input = await openEditor();
    fireEvent.change(input, { target: { value: 'Discard this' } });
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
    input = await openEditor();
    expect((input as HTMLInputElement).value).toBe('Original route');
    fireEvent.keyDown(input, { key: 'Escape' });
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
    expect(patch).not.toHaveBeenCalled();
    expect(document.activeElement).toBe(
      screen.getByRole('button', { name: 'Edit route name' })
    );
  });

  it('rejects whitespace-only names and limits input to the API maximum', async () => {
    renderEditor();
    const input = await openEditor();
    expect(input.getAttribute('maxlength')).toBe('255');
    fireEvent.change(input, { target: { value: '   ' } });
    expect(
      screen.getByText('Enter a route name between 1 and 255 characters.')
    ).toBeDefined();
    fireEvent.submit(input.closest('form')!);
    expect(patch).not.toHaveBeenCalled();
    expect(
      screen.getByRole('button', { name: 'Save' }).matches(':disabled')
    ).toBe(true);
  });

  it('retains a failed edit and allows retry', async () => {
    renderEditor();
    const input = await openEditor();
    fireEvent.change(input, { target: { value: 'Retry this name' } });
    fail = true;
    fireEvent.click(screen.getByRole('button', { name: 'Save' }));
    expect(
      await screen.findByText("Couldn't save the route name. Please try again.")
    ).toBeDefined();
    expect((input as HTMLInputElement).value).toBe('Retry this name');
    fail = false;
    fireEvent.click(screen.getByRole('button', { name: 'Save' }));
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
    expect(await screen.findByText('Retry this name')).toBeDefined();
  });

  it('blocks duplicate saves and dismissal while saving', async () => {
    renderEditor();
    const input = await openEditor();
    fireEvent.change(input, { target: { value: 'Pending name' } });
    pending = new Promise<void>((resolve) => {
      release = resolve;
    });
    fireEvent.click(screen.getByRole('button', { name: 'Save' }));
    await waitFor(() =>
      expect(
        screen.getByRole('button', { name: 'Saving…' }).matches(':disabled')
      ).toBe(true)
    );
    expect(
      screen.getByRole('button', { name: 'Cancel' }).matches(':disabled')
    ).toBe(true);
    fireEvent.keyDown(input, { key: 'Escape' });
    fireEvent.click(screen.getByRole('button', { name: 'Close' }));
    expect(screen.getByRole('dialog')).toBeDefined();
    release!();
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
    expect(patch).toHaveBeenCalledTimes(1);
  });
});
