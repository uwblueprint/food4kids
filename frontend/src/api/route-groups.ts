import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  createRouteGroupMutation,
  deleteRouteGroupMutation,
  duplicateRouteGroupMutation,
  getRouteGroupsOptions,
  getRouteGroupsQueryKey,
  getRoutesQueryKey,
  updateRouteGroupMutation,
} from './generated/@tanstack/react-query.gen';
import type { GetRouteGroupsData } from './generated/types.gen';

/**
 * Fetch the (filtered) list of route groups for the admin routes "Groups" tab.
 *
 * The aggregate fields the tab renders (num_locations, num_boxes,
 * num_drivers_assigned, delivery_type, status) are computed server-side and
 * returned on RouteGroupRead (F4KRP-196). Consumers should import that
 * generated type rather than a hand-written row shape.
 *
 * GET /route-groups has no full-text search param yet, so the tab's search box
 * is local-only UI for now — only the filter chips hit the server.
 */
export function useRouteGroups(query: GetRouteGroupsData['query']) {
  return useQuery({
    ...getRouteGroupsOptions({ query }),
    placeholderData: [],
  });
}

/**
 * POST /route-groups. Invalidates every cached GET /route-groups variant so
 * all filter combinations refetch.
 */
export function useCreateRouteGroup() {
  const queryClient = useQueryClient();
  return useMutation({
    ...createRouteGroupMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: getRouteGroupsQueryKey() });
    },
  });
}

/**
 * PATCH /route-groups/{route_group_id}. Invalidates every cached
 * GET /route-groups variant so all filter combinations refetch, plus
 * GET /routes since each route's drive_date comes from its group.
 *
 * Returns the invalidation promise so per-call onSuccess callbacks run only
 * after the refetched lists land — rows are already re-sorted by then, which
 * the drive-date cell's highlight-and-scroll relies on.
 */
export function useUpdateRouteGroup() {
  const queryClient = useQueryClient();
  return useMutation({
    ...updateRouteGroupMutation(),
    onSuccess: () =>
      Promise.all([
        queryClient.invalidateQueries({ queryKey: getRouteGroupsQueryKey() }),
        queryClient.invalidateQueries({ queryKey: getRoutesQueryKey() }),
      ]),
  });
}

/**
 * DELETE /route-groups/{route_group_id}. Invalidates GET /route-groups and
 * GET /routes since the group's routes are cascade-deleted with it.
 */
export function useDeleteRouteGroup() {
  const queryClient = useQueryClient();
  return useMutation({
    ...deleteRouteGroupMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: getRouteGroupsQueryKey() });
      queryClient.invalidateQueries({ queryKey: getRoutesQueryKey() });
    },
  });
}

/**
 * POST /route-groups/{route_group_id}/duplicate. The optional body overrides
 * the copy's name and drive_date. Invalidates GET /route-groups and
 * GET /routes since the group's routes are copied with it.
 */
export function useDuplicateRouteGroup() {
  const queryClient = useQueryClient();
  return useMutation({
    ...duplicateRouteGroupMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: getRouteGroupsQueryKey() });
      queryClient.invalidateQueries({ queryKey: getRoutesQueryKey() });
    },
  });
}
