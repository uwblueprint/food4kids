import { useQuery } from '@tanstack/react-query';

import axiosClient from '@/lib/axiosClient';

// WIP shell: this hook is still hand-written, and RouteGroupRow is the shape
// the Groups tab wants — not a generated API type, since the backend doesn't
// return these aggregates yet (F4KRP-196). When it does, swap RouteGroupRow
// for the generated type here and convert useRouteGroups to the generated
// client; consumers importing RouteGroupRow from this module stay unchanged.
export type RouteStatus = 'Upcoming' | 'Completed' | 'Archived';

export interface RouteGroupRow {
  id: string;
  name: string;
  date: string;
  delivery_type: string;
  num_routes: number;
  num_locations: number;
  num_boxes: number;
  num_drivers_assigned: number;
  status: RouteStatus;
}

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
