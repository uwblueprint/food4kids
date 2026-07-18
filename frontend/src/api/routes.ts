import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  deleteRouteMutation,
  getRouteGroupsQueryKey,
  getRoutesOptions,
  getRoutesQueryKey,
  updateRouteMutation,
} from './generated/@tanstack/react-query.gen';

export function useRoutes() {
  return useQuery(getRoutesOptions());
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
