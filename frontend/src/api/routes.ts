import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  deleteRouteMutation,
  getRouteGroupsQueryKey,
  getRouteOptions,
  getRouteQueryKey,
  getRoutesOptions,
  getRoutesQueryKey,
  getSuggestedDriverOptions,
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
 * PATCH /routes/{route_id} — driver reassignment or stop edits (the
 * `location_ids` field replaces the route's stops and re-runs routing).
 *
 * Invalidates GET /routes plus GET /route-groups since group aggregates
 * (driver counts) derive from their routes, and the single-route detail
 * (GET /routes/{route_id}) so the individual-route screen reflects the edit.
 */
export function useUpdateRoute() {
  const queryClient = useQueryClient();
  return useMutation({
    ...updateRouteMutation(),
    onSuccess: (_data, variables) =>
      Promise.all([
        queryClient.invalidateQueries({ queryKey: getRoutesQueryKey() }),
        queryClient.invalidateQueries({ queryKey: getRouteGroupsQueryKey() }),
        queryClient.invalidateQueries({
          queryKey: getRouteQueryKey({
            path: { route_id: variables.path.route_id },
          }),
        }),
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

/**
 * GET /routes/{route_id}/suggested-driver — the active driver most familiar
 * with this route's stops, for the assign-driver dialog's hint. Only fetched
 * while `enabled` (the dialog is open), since it is a per-open suggestion
 * rather than something any list needs.
 */
export function useSuggestedDriver(
  routeId: string,
  routeGroupId: string,
  enabled = true
) {
  return useQuery({
    ...getSuggestedDriverOptions({
      path: { route_id: routeId },
      query: { route_group_id: routeGroupId },
    }),
    enabled,
  });
}
