import { useQuery } from '@tanstack/react-query';

import {
  getRouteDeleteImpact,
  getRouteGroupDeleteImpact,
} from './generated/sdk.gen';

export function useRouteDeletionImpact(
  kind: 'route' | 'route group',
  id: string
) {
  return useQuery({
    queryKey: ['routeDeletionImpact', kind, id],
    queryFn: async ({ signal }) => {
      const options = { signal, throwOnError: true } as const;
      const { data } =
        kind === 'route'
          ? await getRouteDeleteImpact({ ...options, path: { route_id: id } })
          : await getRouteGroupDeleteImpact({
              ...options,
              path: { route_group_id: id },
            });
      return data;
    },
  });
}
