import { useQuery } from '@tanstack/react-query';

import { getRouteGroupsOptions } from './generated/@tanstack/react-query.gen';
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
