import axios, { AxiosResponse, InternalAxiosRequestConfig } from "axios";
import { camelizeKeys, decamelizeKeys } from "humps";
import { jwtDecode } from "jwt-decode";

import AUTHENTICATED_USER_KEY from "../constants/AuthConstants";
import { DecodedJWT } from "../types/AuthTypes";
import { setLocalStorageObjProperty } from "../utils/LocalStorageUtils";

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

    // if access token in header has expired, do a refresh
    const authHeader = config.headers?.Authorization;
    const authHeaderParts =
      typeof authHeader === "string" ? authHeader.split(" ") : null;
    if (
      authHeaderParts &&
      authHeaderParts.length >= 2 &&
      authHeaderParts[0].toLowerCase() === "bearer"
    ) {
      const decodedToken = jwtDecode(authHeaderParts[1]) as DecodedJWT;

      if (
        decodedToken &&
        (typeof decodedToken === "string" ||
          decodedToken.exp <= Math.round(new Date().getTime() / 1000))
      ) {
        const { data } = await axios.post(
          `${import.meta.env.VITE_BACKEND_URL}/auth/refresh`,
          {},
          { withCredentials: true },
        );

        const accessToken = data.accessToken || data.access_token;
        setLocalStorageObjProperty(
          AUTHENTICATED_USER_KEY,
          "accessToken",
          accessToken,
        );

        newConfig.headers = newConfig.headers || {};
        newConfig.headers.Authorization = accessToken;
      }
    }

    if (config.params) {
      newConfig.params = decamelizeKeys(config.params);
    }
    if (config.data && !(config.data instanceof FormData)) {
      newConfig.data = decamelizeKeys(config.data);
    }

    return newConfig;
  },
);

export default baseAPIClient;
