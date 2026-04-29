import { useQuery } from '@tanstack/react-query';

import axiosClient from '@/lib/axiosClient';
import type { AddressRow } from '@/types/address';

export interface AddressesParams {
  search?: string;
  routeStatuses?: string[];
  deliveryTypes?: string[];
}

async function fetchAddresses(params: AddressesParams): Promise<AddressRow[]> {
  const response = await axiosClient.get<AddressRow[]>('/addresses', {
    params,
  });
  return response.data;
}

export function useAddresses(params: AddressesParams) {
  return useQuery({
    queryKey: ['addresses', params],
    queryFn: () => fetchAddresses(params),
    placeholderData: [],
  });
}
