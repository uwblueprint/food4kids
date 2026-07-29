import { useMutation, useQueryClient } from '@tanstack/react-query';

import { getSystemSettingsQueryKey } from './generated/@tanstack/react-query.gen';
import { ingestLocations, reviewLocations } from './generated/sdk.gen';
import type { LocationIngestRequest } from './generated/types.gen';

export function useReviewLocations() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      file,
      columnMap,
      deliveryType,
    }: {
      file: File;
      columnMap: Record<string, string>;
      deliveryType: string;
    }) => {
      const { data } = await reviewLocations({
        body: {
          file,
          column_map: JSON.stringify(columnMap),
          delivery_type: deliveryType,
        },
        throwOnError: true,
      });
      return data;
    },
    onSuccess: () => {
      // Backend persists the submitted column_map as the new default
      queryClient.invalidateQueries({ queryKey: getSystemSettingsQueryKey() });
    },
  });
}

export function useIngestLocations() {
  return useMutation({
    mutationFn: async (request: LocationIngestRequest) => {
      const { data } = await ingestLocations({
        body: request,
        throwOnError: true,
      });
      return data;
    },
  });
}
