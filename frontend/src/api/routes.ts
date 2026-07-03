import { useQuery } from '@tanstack/react-query';

import { getRoutesOptions } from './generated/@tanstack/react-query.gen';

export function useRoutes() {
  return useQuery(getRoutesOptions());
}
