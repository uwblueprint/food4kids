// @vitest-environment happy-dom
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
} from '@testing-library/react';
import type { AxiosResponse, InternalAxiosRequestConfig } from 'axios';
import { AxiosError } from 'axios';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { useAuthStore } from '@/api/authStore';
import type { AuthResponse } from '@/api/generated';
import axiosClient from '@/lib/axiosClient';

import { AuthProvider, RESTORE_GRACE_MS } from './AuthProvider';

// The startup session restore, driven through the real axiosClient with a fake
// adapter: what the visitor sees while it runs, and which failures end it.

const SESSION: AuthResponse = {
  access_token: 'token-xyz',
  email: 'dana@example.com',
  first_name: 'Dana',
  full_name: 'Dana Bell',
  id: 'user-1',
  last_name: 'Bell',
  remember_me: false,
  role: 'Admin',
};

type Reply =
  | { session: AuthResponse }
  | { status: number }
  | { networkError: true };

const realAdapter = axiosClient.defaults.adapter;

// Each refresh hangs until the test calls `answer`, so a test can look at the
// page mid-flight and then choose the outcome.
let answer!: (reply: Reply) => void;
let pendingReply: Promise<Reply>;

function armReply() {
  pendingReply = new Promise<Reply>((resolve) => {
    answer = resolve;
  });
}

/** Let `ms` of real time pass, with React free to apply whatever settled. */
async function advance(ms: number) {
  await act(async () => {
    await new Promise((resolve) => setTimeout(resolve, ms));
  });
}

async function fakeAdapter(config: InternalAxiosRequestConfig) {
  const reply = await pendingReply;

  if ('networkError' in reply) {
    throw new AxiosError('Network Error', AxiosError.ERR_NETWORK, config);
  }

  const status = 'session' in reply ? 200 : reply.status;
  const response = {
    data: 'session' in reply ? reply.session : { detail: 'nope' },
    status,
    statusText: '',
    headers: {},
    config,
  } as AxiosResponse;

  if (status >= 400) {
    throw new AxiosError(
      `Request failed with status code ${status}`,
      AxiosError.ERR_BAD_REQUEST,
      config,
      null,
      response
    );
  }
  return response;
}

function renderApp() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route path="/login" element={<div>Login page</div>} />
          <Route
            path="*"
            element={
              <AuthProvider>
                <div>Protected page</div>
              </AuthProvider>
            }
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

beforeEach(() => {
  armReply();
  useAuthStore.getState().clearAuth();
  useAuthStore.setState({ isRestoringSession: true });
  axiosClient.defaults.adapter = fakeAdapter;
});

afterEach(async () => {
  // axiosClient shares one in-flight refresh, so never leave it hanging.
  answer({ networkError: true });
  await advance(0);
  cleanup();
  axiosClient.defaults.adapter = realAdapter;
});

describe('while the session is being restored', () => {
  it('renders nothing at all inside the grace window', async () => {
    const { container } = renderApp();

    expect(container.innerHTML).toBe('');

    await advance(RESTORE_GRACE_MS / 2);
    expect(container.innerHTML).toBe('');
    expect(screen.queryByText(/restoring your session/i)).toBeNull();
  });

  it('explains itself once the grace window has passed', async () => {
    renderApp();

    expect(await screen.findByText(/restoring your session/i)).toBeTruthy();
  });

  it('shows nothing on the way in when the refresh lands promptly', async () => {
    const { container } = renderApp();
    answer({ session: SESSION });

    expect(container.innerHTML).toBe('');
    expect(await screen.findByText('Protected page')).toBeTruthy();
    expect(screen.queryByText(/restoring your session/i)).toBeNull();
  });
});

describe('when the refresh fails', () => {
  // Every 4xx is the server rejecting the cookie, and a retry would repeat it.
  it.each([400, 401, 403, 404])(
    'sends a visitor with no session to the login page on a %i',
    async (status) => {
      renderApp();
      answer({ status });

      expect(await screen.findByText('Login page')).toBeTruthy();

      const state = useAuthStore.getState();
      expect(state.isRestoringSession).toBe(false);
      expect(state.isAuthenticated).toBe(false);
      expect(state.accessToken).toBeNull();
    }
  );

  // The bug this file was written for: a blip used to clear the store and
  // sign out someone whose refresh cookie was still good.
  it.each([
    ['a connection that never landed', { networkError: true } as const],
    ['a 500 from the server', { status: 500 } as const],
    ['a 503 from the server', { status: 503 } as const],
  ])('leaves the session alone on %s', async (_label, reply) => {
    renderApp();
    answer(reply);

    expect(
      await screen.findByRole('button', { name: /try again/i })
    ).toBeTruthy();

    expect(useAuthStore.getState().isRestoringSession).toBe(true);
    expect(screen.queryByText('Login page')).toBeNull();
  });

  it('keeps even the failure silent until the grace window has passed', async () => {
    const { container } = renderApp();
    answer({ networkError: true });

    await advance(RESTORE_GRACE_MS - 100);
    expect(container.innerHTML).toBe('');

    expect(
      await screen.findByRole('button', { name: /try again/i })
    ).toBeTruthy();
  });

  it('restores the session when the retry succeeds', async () => {
    renderApp();
    answer({ networkError: true });

    const retry = await screen.findByRole('button', { name: /try again/i });

    armReply();
    fireEvent.click(retry);
    answer({ session: SESSION });

    expect(await screen.findByText('Protected page')).toBeTruthy();
    expect(useAuthStore.getState().isAuthenticated).toBe(true);
  });
});
