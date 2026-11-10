import { useQuery } from '@tanstack/react-query';

import axiosClient, { API_BASE_URL } from '@/lib/axiosClient';

import { getBillingCostsOptions } from './generated/@tanstack/react-query.gen';

export function useBillingCosts() {
  return useQuery({
    ...getBillingCostsOptions({ axios: axiosClient, baseURL: API_BASE_URL }),
    // Billing exports lag by hours; avoid refetching on every homepage visit.
    staleTime: 5 * 60 * 1000,
  });
}
