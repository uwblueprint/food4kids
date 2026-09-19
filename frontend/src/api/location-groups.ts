import { useQuery } from '@tanstack/react-query';

import { getLocationGroupsOptions } from './generated/@tanstack/react-query.gen';

export function useLocationGroups() {
  return useQuery(getLocationGroupsOptions());
}
