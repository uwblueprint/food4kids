import { useQuery } from '@tanstack/react-query';

import { getRouteOptions } from '@/api/generated/@tanstack/react-query.gen';

export function useRoute(routeId: string | undefined) {
  return useQuery({
    ...getRouteOptions({ path: { route_id: routeId ?? '' } }),
    enabled: !!routeId,
  });
}
