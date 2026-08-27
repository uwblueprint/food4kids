import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  deleteRouteMutation,
  getRouteGroupsQueryKey,
  getRouteOptions,
  getRoutesOptions,
  getRoutesQueryKey,
  updateRouteMutation,
} from './generated/@tanstack/react-query.gen';
import type { GetRoutesData } from './generated/types.gen';

/**
 * GET /routes for the admin routes "Routes" tab.
 *
 * The `search` query filters (case-insensitive) on the assigned driver's name
 * server-side, before pagination. Keeps the previous page visible while a new
 * search refetches so the table doesn't flash empty.
 */
export function useRoutes(query?: GetRoutesData['query']) {
  return useQuery({
    ...getRoutesOptions({ query }),
    placeholderData: (prev) => prev,
  });
}

/**
 * GET /routes for driver's assigned routes (filtered by driver_id).
 * Drivers are automatically scoped to their own routes when driver_id is omitted.
 */
export function useDriverRoutes() {
  return useQuery({
    ...getRoutesOptions({ query: { page: 1, page_size: 100 } }),
  });
}

/**
 * GET /routes/{route_id} to fetch a single route with full details including encoded_polyline.
 */
export function useRoute(routeId: string) {
  return useQuery(
    getRouteOptions({
      path: { route_id: routeId },
    })
  );
}

/**
 * PATCH /routes/{route_id} (e.g. driver reassignment). Invalidates
 * GET /routes plus GET /route-groups since group aggregates (driver counts)
 * derive from their routes.
 */
export function useUpdateRoute() {
  const queryClient = useQueryClient();
  return useMutation({
    ...updateRouteMutation(),
    onSuccess: () =>
      Promise.all([
        queryClient.invalidateQueries({ queryKey: getRoutesQueryKey() }),
        queryClient.invalidateQueries({ queryKey: getRouteGroupsQueryKey() }),
      ]),
  });
}

/**
 * DELETE /routes/{route_id}. Invalidates GET /routes plus GET /route-groups
 * since group aggregates (route/driver counts) derive from their routes.
 */
export function useDeleteRoute() {
  const queryClient = useQueryClient();
  return useMutation({
    ...deleteRouteMutation(),
    onSuccess: () =>
      Promise.all([
        queryClient.invalidateQueries({ queryKey: getRoutesQueryKey() }),
        queryClient.invalidateQueries({ queryKey: getRouteGroupsQueryKey() }),
      ]),
  });
}
