import axios, { isAxiosError } from 'axios';

import { useAuthStore } from '@/api/authStore';

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

// A 401 means the token we sent is no longer good — expired, or revoked out
// from under us. There is nothing to retry with: revocation invalidates the
// refresh token too, so the session is genuinely over and the only way forward
// is logging in again. Clearing auth is enough to get there; `AuthProvider`
// already sends an unauthenticated visitor to /login.
//
// Only requests that actually carried a token count. Without this guard, the
// session-restore call that 401s on every first visit — the ordinary state of
// someone who simply is not logged in — would announce an expired session to a
// person who never had one.
//
// A 403 is deliberately left alone. It means the server knows exactly who we
// are and this is not ours; logging in again would land the same 403, so
// bouncing to the login page would only produce a loop.
axiosClient.interceptors.response.use(undefined, (error: unknown) => {
  if (isAxiosError(error) && error.response?.status === 401) {
    if (error.config?.headers?.Authorization) {
      useAuthStore.getState().expireSession();
    }
  }
  return Promise.reject(error);
});

export default axiosClient;
