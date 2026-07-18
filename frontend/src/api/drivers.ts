import { useQuery } from '@tanstack/react-query';

import { getDriversOptions } from './generated/@tanstack/react-query.gen';

/** Fetch the list of drivers (e.g. for the reassign-driver dropdown). */
export function useDrivers() {
  return useQuery(getDriversOptions());
}
