import { useQuery } from '@tanstack/react-query';

import axiosClient from '@/lib/axiosClient';
import type { Route } from '@/types/route';

export function useRoute(routeId: string | undefined) {
  return useQuery({
    queryKey: ['route', routeId],
    queryFn: async () => {
      const { data } = await axiosClient.get<Route>(`/routes/${routeId}`);
      return data;
    },
    enabled: !!routeId,
  });
}