import { useQuery } from '@tanstack/react-query';

import axiosClient from '@/lib/axiosClient';
import type { RouteGroupRow } from '@/types/route-group';

export interface RouteGroupsParams {
  search?: string;
  weekdays?: string[];
  deliveryTypes?: string[];
  routeStatuses?: string[];
  driverStatuses?: string[];
}

async function fetchRouteGroups(
  params: RouteGroupsParams
): Promise<RouteGroupRow[]> {
  const response = await axiosClient.get<RouteGroupRow[]>('/route-groups', {
    params,
  });
  return response.data;
}

export function useRouteGroups(params: RouteGroupsParams) {
  return useQuery({
    queryKey: ['route-groups', params],
    queryFn: () => fetchRouteGroups(params),
    placeholderData: [],
  });
}
