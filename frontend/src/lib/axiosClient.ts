import axios from 'axios';

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

export default axiosClient;
