import axios from 'axios';

import { useAuthStore } from '@/api/authStore';

const axiosClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8080',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

axiosClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

axiosClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config as
      | (typeof error.config & { _authRetry?: boolean })
      | undefined;

    const status = error.response?.status;
    const shouldRetryAuth =
      import.meta.env.DEV &&
      originalRequest &&
      !originalRequest._authRetry &&
      (status === 401 || status === 403);

    if (shouldRetryAuth) {
      originalRequest._authRetry = true;
      invalidateAuthSession();
      const loggedIn = await ensureAuthSession();
      const token = getAccessToken();
      if (loggedIn && token) {
        originalRequest.headers.Authorization = `Bearer ${token}`;
        return axiosClient(originalRequest);
      }
    }

    return Promise.reject(error);
  }
);

export default axiosClient;
