import type { QueryClient } from '@tanstack/react-query';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  getLocationsOptions,
  getSystemSettingsQueryKey,
} from './generated/@tanstack/react-query.gen';
import {
  applyLocationImport,
  previewLocationImport,
} from './generated/sdk.gen';
import type { GetLocationsData } from './generated/types.gen';

/**
 * GET /locations for pickers (e.g. adding a stop to a route). The `search`
 * query filters case-insensitively on the address server-side, before
 * pagination; `placeholderData` keeps the previous page visible while a new
 * search refetches so the list doesn't flash empty.
 */
export function useLocations(query?: GetLocationsData['query']) {
  return useQuery({
    ...getLocationsOptions({ query }),
    placeholderData: (prev) => prev,
  });
}

/**
 * Preview and apply take the same input on purpose: the backend plans the
 * import from the file both times, so applying can't act on anything the
 * preview didn't show.
 */
export interface LocationImportRequest {
  file: File;
  columnMap: Record<string, string>;
  deliveryType: string;
}

const toBody = ({ file, columnMap, deliveryType }: LocationImportRequest) => ({
  file,
  column_map: JSON.stringify(columnMap),
  delivery_type: deliveryType,
});

// Both endpoints persist the submitted column_map as the new default.
const invalidateSystemSettings = (queryClient: QueryClient) =>
  queryClient.invalidateQueries({ queryKey: getSystemSettingsQueryKey() });

export function usePreviewLocationImport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (request: LocationImportRequest) => {
      const { data } = await previewLocationImport({
        body: toBody(request),
        throwOnError: true,
      });
      return data;
    },
    onSuccess: () => invalidateSystemSettings(queryClient),
  });
}

export function useApplyLocationImport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (request: LocationImportRequest) => {
      const { data } = await applyLocationImport({
        body: toBody(request),
        throwOnError: true,
      });
      return data;
    },
    onSuccess: () => invalidateSystemSettings(queryClient),
  });
}
