import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  deleteRouteMutation,
  getRouteGroupsQueryKey,
  getRouteQueryKey,
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
