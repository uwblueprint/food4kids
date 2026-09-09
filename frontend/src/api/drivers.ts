import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  deleteDriverMutation,
  getDriverHistorySummaryOptions,
  getDriverOptions,
  getDriversOptions,
  getDriversQueryKey,
  initializeDriverMutation,
  updateDriverMutation,
} from './generated/@tanstack/react-query.gen';
import type { GetDriversData } from './generated/types.gen';

export function useDriverList(query?: GetDriversData['query']) {
  return useQuery({
    ...getDriversOptions({ query }),
    placeholderData: (previous) => previous,
  });
}

/** Compact driver list used by assignment dropdowns. */
export function useDrivers() {
  return useQuery({
    ...getDriversOptions({ query: { page_size: 200 } }),
    select: (data) => data.items,
  });
}

export function useDriver(driverId: string | null) {
  return useQuery({
    ...getDriverOptions({ path: { driver_id: driverId ?? '' } }),
    enabled: !!driverId,
  });
}

export function useDriverSummary(driverId: string | null) {
  return useQuery({
    ...getDriverHistorySummaryOptions({
      path: { driver_id: driverId ?? '' },
    }),
    enabled: !!driverId,
  });
}

function invalidateDrivers(queryClient: ReturnType<typeof useQueryClient>) {
  return queryClient.invalidateQueries({ queryKey: getDriversQueryKey() });
}

export function useInitializeDriver() {
  const queryClient = useQueryClient();
  return useMutation({
    ...initializeDriverMutation(),
    onSuccess: () => invalidateDrivers(queryClient),
  });
}

export function useUpdateDriver() {
  const queryClient = useQueryClient();
  return useMutation({
    ...updateDriverMutation(),
    onSuccess: () => invalidateDrivers(queryClient),
  });
}

export function useDeleteDriver() {
  const queryClient = useQueryClient();
  return useMutation({
    ...deleteDriverMutation(),
    onSuccess: () => invalidateDrivers(queryClient),
  });
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
