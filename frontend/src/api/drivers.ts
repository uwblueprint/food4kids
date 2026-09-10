import { useQuery } from '@tanstack/react-query';

import {
  getDriverHistorySummaryOptions,
  getDriverOptions,
  getDriversOptions,
} from './generated/@tanstack/react-query.gen';

/** Fetch the list of drivers (e.g. for the reassign-driver dropdown). */
export function useDrivers() {
  return useQuery(getDriversOptions());
}

/** Fetch a single driver by ID. */
export function useDriver(driverId: string) {
  return useQuery(
    getDriverOptions({
      path: { driver_id: driverId },
    })
  );
}

/** Fetch driver's lifetime and current year KM summary. */
export function useDriverHistorySummary(driverId: string, enabled = true) {
  return useQuery({
    ...getDriverHistorySummaryOptions({
      path: { driver_id: driverId },
    }),
    enabled: enabled && !!driverId,
  });
}
