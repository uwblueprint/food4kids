import { useMutation, useQueryClient } from '@tanstack/react-query';

import { getSystemSettingsQueryKey } from './generated/@tanstack/react-query.gen';
import { reviewLocations } from './generated/sdk.gen';

export function useReviewLocations() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      file,
      columnMap,
    }: {
      file: File;
      columnMap: Record<string, string>;
    }) => {
      const { data } = await reviewLocations({
        body: { file, column_map: JSON.stringify(columnMap) },
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
