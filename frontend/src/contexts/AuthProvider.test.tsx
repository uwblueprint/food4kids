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

import { AuthProvider } from './AuthProvider';

/**
 * The startup session restore, end to end: what the visitor sees while it runs,
 * and which outcomes are allowed to end a session.
 *
 * The access token lives in memory only, so every load of a protected route
 * waits on `POST /auth/refresh` before anyone knows who is here. Two things
 * follow, and both are pinned below: the wait must be invisible when it is
 * short, and a refresh that never got an answer must not sign anyone out —
 * that is a dropped connection, not a revoked session, exactly the distinction
 * `axiosClient` already draws mid-session.
 */

/** Must match RESTORE_GRACE_MS in AuthProvider.tsx. */
const GRACE_MS = 300;

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

/**
 * The refresh hangs until the test answers it, so a test can inspect the page
 * mid-flight — which is the whole subject here — and then decide the outcome.
 */
let answer!: (reply: Reply) => void;
let pendingReply: Promise<Reply>;

function armReply() {
  pendingReply = new Promise<Reply>((resolve) => {
    answer = resolve;
  });
}

/**
 * Let real time pass — the grace window is a real timer — while React is free
 * to process whatever the refresh settled in the meantime.
 */
async function advance(ms: number) {
  await act(async () => {
    await new Promise((resolve) => setTimeout(resolve, ms));
  });
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
  useAuthStore.setState({
    accessToken: null,
    user: null,
    isAuthenticated: false,
    isRestoringSession: true,
    sessionExpired: false,
    rememberMe: false,
  });

  axiosClient.defaults.adapter = async (config: InternalAxiosRequestConfig) => {
    const reply = await pendingReply;

    if ('networkError' in reply) {
      throw new AxiosError('Network Error', AxiosError.ERR_NETWORK, config);
    }

    if ('session' in reply) {
      return {
        data: reply.session,
        status: 200,
        statusText: 'OK',
        headers: {},
        config,
      } as AxiosResponse;
    }

    const response = {
      data: { detail: 'nope' },
      status: reply.status,
      statusText: 'Error',
      headers: {},
      config,
    } as AxiosResponse;
    throw new AxiosError(
      `Request failed with status code ${reply.status}`,
      AxiosError.ERR_BAD_REQUEST,
      config,
      null,
      response
    );
  };
});

afterEach(async () => {
  // Never leave a refresh in flight: axiosClient shares one across callers, and
  // a hung one would still be there for the next test.
  answer({ networkError: true });
  await advance(0);
  cleanup();
  axiosClient.defaults.adapter = realAdapter;
  useAuthStore.getState().clearAuth();
});

describe('while the session is being restored', () => {
  it('renders nothing at all inside the grace window', async () => {
    const { container } = renderApp();

    expect(container.innerHTML).toBe('');

    // Still nothing well into the window — not merely a first-paint artifact.
    await advance(GRACE_MS / 2);
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
  it('sends a visitor with no session to the login page on a 401', async () => {
    renderApp();
    answer({ status: 401 });

    expect(await screen.findByText('Login page')).toBeTruthy();

    const state = useAuthStore.getState();
    expect(state.isRestoringSession).toBe(false);
    expect(state.isAuthenticated).toBe(false);
    expect(state.accessToken).toBeNull();
  });

  /**
   * The bug this file was written for. A blip on the way to `/auth/refresh`
   * used to clear the store, signing out someone whose refresh cookie was
   * still perfectly good and bouncing them to the login page.
   */
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

    await advance(GRACE_MS - 100);
    expect(container.innerHTML).toBe('');

    // Non-vacuous: the failure was already in hand, just not yet worth saying.
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
