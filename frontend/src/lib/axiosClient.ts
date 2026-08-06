import axios, { type InternalAxiosRequestConfig, isAxiosError } from 'axios';

import { useAuthStore } from '@/api/authStore';
import type { AuthResponse } from '@/api/generated';

// Transport concerns only: base URL, credentials, auth.
//
// Deliberately no default Content-Type. That is a per-operation fact, and the
// generated SDK already sets it from the OpenAPI spec — `application/json` for
// JSON bodies, and unset for the multipart uploads so the browser can supply
// `multipart/form-data` along with the `boundary` only it can compute.
//
// A default here cannot be overridden by the SDK: it encodes "unset" as a null
// header, which merges as *absent from this request* rather than *cleared*, so
// the instance default silently wins. Axios then sees FormData labelled as JSON
// and re-serializes it (any File becomes `{}`), which the API rejects as a 422.
// See src/lib/axiosClient.test.ts.
const axiosClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8080',
  withCredentials: true,
});

// Attach auth token to every request if present
axiosClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

const REFRESH_PATH = '/auth/refresh';

interface SessionRequestConfig extends InternalAxiosRequestConfig {
  /**
   * Set on the request we re-send once a refresh has succeeded. If a token
   * minted seconds ago is refused too, the problem was never staleness, so
   * there is nothing left to try.
   */
  replayedAfterRefresh?: boolean;
}

/**
 * The refresh currently in flight, shared by everyone waiting on it.
 *
 * A screen that fires several requests at once discovers the same stale token
 * several times over, and each exchange rotates the refresh cookie — so racing
 * them would leave the losers presenting a cookie the winner already spent.
 */
let refreshInFlight: Promise<AuthResponse> | null = null;

/**
 * Trade the httpOnly refresh cookie for a new access token and adopt it.
 *
 * The one thing that knows how to restore a session, whether that is on first
 * load or halfway through one.
 */
export function refreshSession(): Promise<AuthResponse> {
  const pending =
    refreshInFlight ??
    axiosClient
      .post<AuthResponse>(REFRESH_PATH)
      .then(({ data }) => {
        useAuthStore.getState().setAuth(data);
        return data;
      })
      .finally(() => {
        refreshInFlight = null;
      });

  refreshInFlight = pending;
  return pending;
}

/**
 * The generated SDK joins the base URL onto the path before handing the request
 * to axios, while `refreshSession` sends the path on its own, so a refresh
 * arrives here in either shape.
 */
function isRefreshRequest(config: InternalAxiosRequestConfig): boolean {
  return (config.url ?? '').endsWith(REFRESH_PATH);
}

// A 401 says the access token we sent was rejected, and that is two different
// situations wearing one status code. The token may simply have aged out —
// Firebase mints them with an hour of life, so any tab left open for an
// afternoon outlives its token — or the session may have been revoked, which
// kills the refresh cookie alongside it.
//
// Nothing here has to guess which. `/auth/refresh` reads only the httpOnly
// refresh cookie, so asking it *is* the test: it answers with a new access
// token while the session is alive and 401s once it is not. So a 401 is met by
// refreshing and replaying the request, and only a refusal from the refresh
// itself ends the session. `AuthProvider` sends an unauthenticated visitor to
// /login from there.
//
// Only requests that actually carried a token count. Without this guard, the
// session-restore call that 401s on every first visit — the ordinary state of
// someone who simply is not logged in — would announce an expired session to a
// person who never had one.
//
// A 403 is deliberately left alone. It means the server knows exactly who we
// are and this is not ours; logging in again would land the same 403, so
// bouncing to the login page would only produce a loop.
axiosClient.interceptors.response.use(undefined, async (error: unknown) => {
  if (!isAxiosError(error) || error.response?.status !== 401) {
    return Promise.reject(error);
  }

  const config = error.config as SessionRequestConfig | undefined;
  if (!config?.headers?.Authorization) {
    return Promise.reject(error);
  }

  // Two 401s end the line rather than start a refresh: the refresh endpoint's
  // own, which is the server declining to renew the session, and one from a
  // request we already replayed on a token minted moments earlier.
  if (isRefreshRequest(config) || config.replayedAfterRefresh) {
    useAuthStore.getState().expireSession();
    return Promise.reject(error);
  }

  try {
    await refreshSession();
  } catch {
    // Whether that was a refusal or a dropped connection has already been
    // settled by the refresh's own trip through this handler — a refusal ends
    // the session there, a connection that never landed says nothing about the
    // session and leaves it standing. Either way this request has no token to
    // retry with, so hand the caller the 401 they actually got.
    return Promise.reject(error);
  }

  // The request interceptor reads the token from the store, so the replay picks
  // up the new one without being told.
  config.replayedAfterRefresh = true;
  return axiosClient(config);
});

export default axiosClient;
