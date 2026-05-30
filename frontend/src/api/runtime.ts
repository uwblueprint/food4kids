import axiosClient from '@/lib/axiosClient';

import type { CreateClientConfig } from './generated/client.gen';

export const createClientConfig: CreateClientConfig = (config) => ({
  ...config,
  axios: axiosClient,
});
