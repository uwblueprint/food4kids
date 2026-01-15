import axios, { AxiosResponse, InternalAxiosRequestConfig } from 'axios';
import { camelizeKeys, decamelizeKeys } from 'humps';
import { auth } from '../config/firebase';

const baseAPIClient = axios.create({
  baseURL: import.meta.env.VITE_BACKEND_URL,
});

// Python API uses snake_case, frontend uses camelCase
// convert request and response data to/from snake_case and camelCase through axios interceptors
baseAPIClient.interceptors.response.use((response: AxiosResponse) => {
  if (
    response.data &&
    response.headers["content-type"] === "application/json"
  ) {
    response.data = camelizeKeys(response.data);
  }
  return response;
});

baseAPIClient.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    const newConfig = { ...config };

    // Add Firebase ID token to Authorization header
    const user = auth.currentUser;
    if (user) {
      try {
        const idToken = await user.getIdToken();
        newConfig.headers = newConfig.headers || {};
        newConfig.headers.Authorization = `Bearer ${idToken}`;
      } catch (error) {
        console.error('Failed to get ID token:', error);
      }
    }

    // Convert request params to snake_case
    if (config.params) {
      newConfig.params = decamelizeKeys(config.params);
    }

    // Convert request data to snake_case
    if (config.data && !(config.data instanceof FormData)) {
      newConfig.data = decamelizeKeys(config.data);
    }

    return newConfig;
  },
);

export default baseAPIClient;
