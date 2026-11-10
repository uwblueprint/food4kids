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
import { AxiosError } from 'axios';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it } from 'vitest';

import { useAuthStore } from '@/api/authStore';
import type {
  NoteFeedItem,
  PaginatedResponseNoteFeedItem,
} from '@/api/generated/types.gen';
import axiosClient from '@/lib/axiosClient';

import { NoteFeedEntry } from './NoteFeedEntry';
import { RecentNotesCard } from './RecentNotesCard';

const originalAdapter = axiosClient.defaults.adapter;
const clients: QueryClient[] = [];
afterEach(() => {
  cleanup();
  clients.forEach((client) => client.clear());
  clients.length = 0;
  axiosClient.defaults.adapter = originalAdapter;
  useAuthStore.setState({
    isAuthenticated: false,
    accessToken: null,
    user: null,
  });
});

const note: NoteFeedItem = {
  note_id: 'note-1',
  note_chain_id: 'chain-1',
  location_id: 'location-1',
  location_name: 'Waterloo PS',
  location_group_name: 'Monday schools',
  location_address: '123 School Street',
  author_name: 'Alex Driver',
  author_role: 'driver',
  author_email: 'alex@example.com',
  is_read: true,
  created_at: '2026-11-02T15:00:00Z',
  message: 'Please use the side entrance.\nRing the bell on arrival.',
  attachments: [
    { filename: 'entrance.png', url: 'https://example.com/entrance.png' },
  ],
};

function feed(
  items: NoteFeedItem[] = [note],
  page = 1,
  totalPages = 1
): PaginatedResponseNoteFeedItem {
  return {
    items,
    page,
    page_size: 20,
    total: items.length * totalPages,
    total_pages: totalPages,
  };
}

function respond(data: PaginatedResponseNoteFeedItem) {
  axiosClient.defaults.adapter = async (config) => ({
    data,
    status: 200,
    statusText: 'OK',
    headers: {},
    config,
  });
}

function renderCard(authenticated = true) {
  useAuthStore.setState({
    isAuthenticated: authenticated,
    accessToken: authenticated ? 'test-token' : null,
  });
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  clients.push(client);
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <RecentNotesCard />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe('Recent notes on the admin homepage', () => {
  it.each([
    {
      is_system: true,
      author_name: 'Alex',
      expected: 'System',
      created_at: null,
    },
    {
      is_system: false,
      author_name: null,
      expected: 'Unknown author',
      created_at: null,
    },
    {
      is_system: false,
      author_name: '  ',
      expected: 'Unknown author',
      created_at: 'bad-date',
    },
  ])(
    'handles note metadata: $expected, $created_at',
    ({ expected, ...metadata }) => {
      const { container } = render(
        <NoteFeedEntry
          note={{ ...note, ...metadata, attachments: [] }}
          preview
        />
      );
      expect(screen.getByText(expected)).toBeDefined();
      expect(container.querySelector('time')).toBeNull();
      expect(screen.queryByText(/Invalid Date/)).toBeNull();
      expect(screen.queryByRole('img')).toBeNull();
    }
  );

  it('waits for authentication before requesting notes', async () => {
    let requests = 0;
    axiosClient.defaults.adapter = async (config) => {
      requests += 1;
      return {
        data: feed(),
        status: 200,
        statusText: 'OK',
        headers: {},
        config,
      };
    };
    renderCard(false);
    expect(requests).toBe(0);
    useAuthStore.setState({ isAuthenticated: true, accessToken: 'test-token' });
    expect(await screen.findByText('Alex Driver')).toBeDefined();
    expect(requests).toBe(1);
  });

  it('keeps rows visible and disables navigation while the next page loads', async () => {
    let release!: () => void;
    const pending = new Promise<void>((resolve) => {
      release = resolve;
    });
    axiosClient.defaults.adapter = async (config) => {
      const page = Number(
        new URL(config.url!, 'http://localhost').searchParams.get('page')
      );
      if (page === 2) await pending;
      return {
        data: feed(
          [
            {
              ...note,
              note_id: `note-${page}`,
              author_name: page === 1 ? 'Alex Driver' : 'Blair Driver',
            },
          ],
          page,
          2
        ),
        status: 200,
        statusText: 'OK',
        headers: {},
        config,
      };
    };
    renderCard();
    fireEvent.click(screen.getByRole('button', { name: 'View all' }));
    const dialog = await screen.findByRole('dialog');
    await within(dialog).findByRole('button', { name: /Alex Driver/ });
    fireEvent.click(within(dialog).getByRole('button', { name: 'Page 2' }));
    expect(
      within(dialog)
        .getByRole('button', { name: /Alex Driver/ })
        .matches(':disabled')
    ).toBe(true);
    expect(
      within(dialog)
        .getByRole('group', { name: 'Notes pagination' })
        .hasAttribute('disabled')
    ).toBe(true);
    expect(within(dialog).getByRole('combobox').matches(':disabled')).toBe(
      true
    );
    expect(
      within(dialog).queryByRole('status', { name: 'Loading' })
    ).toBeNull();
    release();
    expect(
      await within(dialog).findByRole('button', { name: /Blair Driver/ })
    ).toBeDefined();
    expect(
      within(dialog)
        .getByRole('group', { name: 'Notes pagination' })
        .hasAttribute('disabled')
    ).toBe(false);
  });

  it('clears a selection removed by a refetch so it does not reappear selected later', async () => {
    respond(feed());
    renderCard();
    fireEvent.click(screen.getByRole('button', { name: 'View all' }));
    const dialog = await screen.findByRole('dialog');
    const sort = within(dialog).getByRole('combobox');
    fireEvent.keyDown(sort, { key: 'ArrowDown' });
    fireEvent.click(await screen.findByRole('option', { name: 'Oldest' }));
    fireEvent.click(
      await within(dialog).findByRole('button', { name: /Alex Driver/ })
    );
    respond(feed([]));
    await clients[0].invalidateQueries();
    expect(await within(dialog).findByText('No notes yet.')).toBeDefined();
    expect(
      within(dialog).getByText('Select a note to display it here')
    ).toBeDefined();
    respond(feed());
    await clients[0].invalidateQueries();
    const row = await within(dialog).findByRole('button', {
      name: /Alex Driver/,
    });
    expect(row.getAttribute('aria-pressed')).toBe('false');
    expect(
      within(dialog).getByText('Select a note to display it here')
    ).toBeDefined();
  });

  it('requests a limited recent feed, then loads and displays a full note in All Notes', async () => {
    const requests: unknown[] = [];
    axiosClient.defaults.adapter = async (config) => {
      requests.push({
        url: new URL(config.url!, 'http://localhost').pathname,
        params: Object.fromEntries(
          new URL(config.url!, 'http://localhost').searchParams
        ),
        auth: config.headers.get('Authorization'),
      });
      return {
        data: feed(),
        status: 200,
        statusText: 'OK',
        headers: {},
        config,
      };
    };
    renderCard();
    expect(await screen.findByText('Alex Driver')).toBeDefined();
    expect(screen.getByText(/Waterloo PS - Monday schools/)).toBeDefined();
    const timestamp = document.querySelector('time');
    expect(timestamp?.getAttribute('datetime')).toBe(note.created_at);
    expect(timestamp?.textContent).toMatch(/^\d{1,2}:\d{2}[AP]M$/);
    expect(screen.queryByText('123 School Street')).toBeNull();
    expect(requests[0]).toEqual({
      url: expect.stringMatching(/\/api\/notes$/),
      params: { sort: 'recent', page: '1', page_size: '5' },
      auth: 'Bearer test-token',
    });
    fireEvent.click(screen.getByRole('button', { name: 'View all' }));
    const dialog = await screen.findByRole('dialog');
    expect(
      within(dialog).getByText('Select a note to display it here')
    ).toBeDefined();
    fireEvent.click(
      await within(dialog).findByRole('button', { name: /Alex Driver/ })
    );
    const detail = within(dialog).getByRole('region', {
      name: 'Selected note',
    });
    expect(
      within(dialog)
        .getByRole('link', { name: 'View address' })
        .getAttribute('href')
    ).toBe('/admin/routes?tab=addresses');
    expect(within(detail).getByText(/Ring the bell on arrival/)).toBeDefined();
    expect(
      within(detail)
        .getByRole('img', { name: 'entrance.png' })
        .getAttribute('src')
    ).toBe('https://example.com/entrance.png');
    expect(requests).toContainEqual({
      url: expect.stringMatching(/\/api\/notes$/),
      params: { sort: 'unread', page: '1', page_size: '20' },
      auth: 'Bearer test-token',
    });
    fireEvent.click(
      within(dialog).getAllByRole('button', { name: 'Close' })[0]
    );
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
    expect(document.activeElement).toBe(
      screen.getByRole('button', { name: 'View all' })
    );
  });

  it('paginates on the server, clears selection and resets to page one when sorting', async () => {
    const queries: unknown[] = [];
    axiosClient.defaults.adapter = async (config) => {
      const params = new URL(config.url!, 'http://localhost').searchParams;
      queries.push(Object.fromEntries(params));
      const page = Number(params.get('page'));
      return {
        data: feed(
          [
            {
              ...note,
              note_id: `note-${page}`,
              author_name: page === 1 ? 'Alex Driver' : 'Blair Driver',
            },
          ],
          page,
          2
        ),
        status: 200,
        statusText: 'OK',
        headers: {},
        config,
      };
    };
    renderCard();
    fireEvent.click(screen.getByRole('button', { name: 'View all' }));
    const dialog = await screen.findByRole('dialog');
    fireEvent.click(
      await within(dialog).findByRole('button', { name: /Alex Driver/ })
    );
    fireEvent.click(within(dialog).getByRole('button', { name: 'Page 2' }));
    expect(
      await within(dialog).findByRole('button', { name: /Blair Driver/ })
    ).toBeDefined();
    expect(
      within(dialog).getByText('Select a note to display it here')
    ).toBeDefined();
    const select = within(dialog).getByRole('combobox', { name: 'Sort by:' });
    fireEvent.keyDown(select, { key: 'ArrowDown' });
    fireEvent.click(await screen.findByRole('option', { name: 'Oldest' }));
    await waitFor(() =>
      expect(queries).toContainEqual({
        sort: 'oldest',
        page: '1',
        page_size: '20',
      })
    );
    expect(
      await within(dialog).findByRole('button', { name: /Alex Driver/ })
    ).toBeDefined();
    for (const [label, sort] of [
      ['Driver (A–Z)', 'driver'],
      ['Location (A–Z)', 'location'],
    ]) {
      fireEvent.keyDown(select, { key: 'ArrowDown' });
      fireEvent.click(await screen.findByRole('option', { name: label }));
      await waitFor(() =>
        expect(queries).toContainEqual({ sort, page: '1', page_size: '20' })
      );
    }
  });

  it('shows empty states in the widget and modal', async () => {
    respond(feed([]));
    renderCard();
    expect(await screen.findByText('No notes yet.')).toBeDefined();
    fireEvent.click(screen.getByRole('button', { name: 'View all' }));
    const dialog = await screen.findByRole('dialog');
    expect(await within(dialog).findByText('No notes yet.')).toBeDefined();
    expect(
      within(dialog).getByText('Select a note to display it here')
    ).toBeDefined();
  });

  it('retries a failed All Notes request and resets selection when reopened', async () => {
    respond(feed());
    renderCard();
    await screen.findByText('Alex Driver');
    axiosClient.defaults.adapter = async () => {
      throw new AxiosError('Unavailable');
    };
    fireEvent.click(screen.getByRole('button', { name: 'View all' }));
    const dialog = await screen.findByRole('dialog');
    expect(
      await within(dialog).findByText("Couldn't load notes.")
    ).toBeDefined();
    respond(feed());
    fireEvent.click(within(dialog).getByRole('button', { name: 'Retry' }));
    fireEvent.click(
      await within(dialog).findByRole('button', { name: /Alex Driver/ })
    );
    fireEvent.click(
      within(dialog).getAllByRole('button', { name: 'Close' })[0]
    );
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
    fireEvent.click(screen.getByRole('button', { name: 'View all' }));
    expect(
      within(await screen.findByRole('dialog')).getByText(
        'Select a note to display it here'
      )
    ).toBeDefined();
  });

  it('shows loading and recovers from a failed request using Retry', async () => {
    axiosClient.defaults.adapter = async () => {
      throw new AxiosError('Unavailable');
    };
    renderCard();
    expect(screen.getByRole('status', { name: 'Loading' })).toBeDefined();
    expect(
      await screen.findByText("Couldn't load recent notes.")
    ).toBeDefined();
    respond(feed());
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }));
    expect(await screen.findByText('Alex Driver')).toBeDefined();
  });
  it('searches on the server and resets pagination and detail selection', async () => {
    const queries: Record<string, string>[] = [];
    axiosClient.defaults.adapter = async (config) => {
      const params = Object.fromEntries(
        new URL(config.url!, 'http://localhost').searchParams
      );
      queries.push(params);
      const page = Number(params.page);
      return {
        data: params.search
          ? feed(params.search === 'bell' ? [note] : [])
          : feed(
              [
                {
                  ...note,
                  author_name: page === 1 ? 'Alex Driver' : 'Blair Driver',
                },
              ],
              page,
              2
            ),
        status: 200,
        statusText: 'OK',
        headers: {},
        config,
      };
    };
    renderCard();
    fireEvent.click(screen.getByRole('button', { name: 'View all' }));
    const dialog = await screen.findByRole('dialog');
    await within(dialog).findByRole('button', { name: /Alex Driver/ });
    fireEvent.click(within(dialog).getByRole('button', { name: 'Page 2' }));
    fireEvent.click(
      await within(dialog).findByRole('button', { name: /Blair Driver/ })
    );
    fireEvent.change(
      within(dialog).getByRole('textbox', { name: 'Search notes' }),
      { target: { value: 'bell' } }
    );
    await waitFor(() =>
      expect(queries).toContainEqual({
        sort: 'unread',
        page: '1',
        page_size: '20',
        search: 'bell',
      })
    );
    expect(
      await within(dialog).findByRole('button', { name: /Alex Driver/ })
    ).toBeDefined();
    expect(within(dialog).getByText('Nothing selected')).toBeDefined();
    fireEvent.change(
      within(dialog).getByRole('textbox', { name: 'Search notes' }),
      { target: { value: 'absent' } }
    );
    expect(
      await within(dialog).findByText('No results. Try being less specific.')
    ).toBeDefined();
  });

  it('marks unread notes as read with retry and preserves detail when unread sorting moves the note off-page', async () => {
    let read = false;
    let failRead = true;
    let writes = 0;
    axiosClient.defaults.adapter = async (config) => {
      if (config.method === 'post') {
        writes += 1;
        if (failRead) throw new AxiosError('Unavailable');
        read = true;
        return {
          data: undefined,
          status: 204,
          statusText: 'No Content',
          headers: {},
          config,
        };
      }
      const params = new URL(config.url!, 'http://localhost').searchParams;
      const items =
        read && params.get('sort') === 'unread'
          ? [
              {
                ...note,
                note_id: 'other',
                author_name: 'Another Driver',
                message: 'Another note',
              },
            ]
          : [{ ...note, is_read: read }];
      return {
        data: feed(items),
        status: 200,
        statusText: 'OK',
        headers: {},
        config,
      };
    };
    renderCard();
    fireEvent.click(screen.getByRole('button', { name: 'View all' }));
    const dialog = await screen.findByRole('dialog');
    expect(
      within(dialog)
        .getByRole('button', { name: 'View address' })
        .matches(':disabled')
    ).toBe(true);
    expect(
      within(dialog)
        .getByRole('button', { name: 'Email driver' })
        .matches(':disabled')
    ).toBe(true);
    fireEvent.click(
      await within(dialog).findByRole('button', { name: /Alex Driver/ })
    );
    expect(
      await within(dialog).findByText(/Couldn't mark this note as read/)
    ).toBeDefined();
    failRead = false;
    fireEvent.click(
      within(dialog).getByRole('button', { name: 'Retry marking as read' })
    );
    expect(
      await within(dialog).findByRole('button', { name: /Another Driver/ })
    ).toBeDefined();
    expect(
      within(
        within(dialog).getByRole('region', { name: 'Selected note' })
      ).getByText(/Ring the bell on arrival/)
    ).toBeDefined();
    expect(
      within(dialog)
        .getByRole('link', { name: 'Email driver' })
        .getAttribute('href')
    ).toBe('mailto:alex%40example.com');
    expect(writes).toBe(2);
  });

  it('uses Newest for recent sorting and does not email system notes', async () => {
    const sorts: string[] = [];
    axiosClient.defaults.adapter = async (config) => {
      sorts.push(
        new URL(config.url!, 'http://localhost').searchParams.get('sort')!
      );
      return {
        data: feed([{ ...note, is_system: true }]),
        status: 200,
        statusText: 'OK',
        headers: {},
        config,
      };
    };
    renderCard();
    fireEvent.click(screen.getByRole('button', { name: 'View all' }));
    const dialog = await screen.findByRole('dialog');
    fireEvent.keyDown(within(dialog).getByRole('combobox'), {
      key: 'ArrowDown',
    });
    fireEvent.click(await screen.findByRole('option', { name: 'Newest' }));
    const systemRow = await within(dialog).findByRole('button', {
      name: /System/,
    });
    await waitFor(() => expect(systemRow.matches(':disabled')).toBe(false));
    fireEvent.click(systemRow);
    expect(sorts).toContain('recent');
    expect(
      within(dialog)
        .getByRole('button', { name: 'Email driver' })
        .matches(':disabled')
    ).toBe(true);
    expect(
      within(dialog).getByRole('link', { name: 'View address' })
    ).toBeDefined();
  });
  it('does not reuse another admin’s read-state cache or placeholder rows', async () => {
    let release!: () => void;
    const pending = new Promise<void>((resolve) => {
      release = resolve;
    });
    const user = {
      id: 'admin-a',
      firstName: 'A',
      lastName: 'Admin',
      email: 'a@example.com',
      fullName: 'A Admin',
      role: 'admin',
      driverId: null,
      adminId: 'admin-a',
    };
    useAuthStore.setState({ user });
    axiosClient.defaults.adapter = async (config) => {
      const isB = useAuthStore.getState().user?.id === 'admin-b';
      if (isB) await pending;
      return {
        data: feed([
          {
            ...note,
            author_name: isB ? 'Second admin feed' : 'First admin feed',
            is_read: !isB,
          },
        ]),
        status: 200,
        statusText: 'OK',
        headers: {},
        config,
      };
    };
    renderCard();
    fireEvent.click(screen.getByRole('button', { name: 'View all' }));
    const dialog = await screen.findByRole('dialog');
    await within(dialog).findByRole('button', { name: /First admin feed/ });
    useAuthStore.setState({ user: { ...user, id: 'admin-b' } });
    await waitFor(() =>
      expect(
        within(screen.getByRole('dialog')).queryByRole('button', {
          name: /First admin feed/,
        })
      ).toBeNull()
    );
    release();
    expect(
      await within(screen.getByRole('dialog')).findByRole('button', {
        name: /Second admin feed/,
      })
    ).toBeDefined();
  });
});
