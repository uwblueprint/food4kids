import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  deleteLocationMutation,
  getLocationsOptions,
  getLocationsQueryKey,
} from './generated/@tanstack/react-query.gen';
import type { GetLocationsData } from './generated/types.gen';

/**
 * Fetch the (paginated) list of locations for the admin routes "Addresses" tab.
 *
 * The status and delivery_type filters reach the server; GET /locations has no
 * full-text search param yet, so the tab's search box is local-only UI (see
 * useAddressesTabState).
 */
export function useAddresses(query?: GetLocationsData['query']) {
  return useQuery({
    ...getLocationsOptions({ query }),
    placeholderData: (prev) => prev,
  });
}

/** DELETE /locations/{location_id}. Invalidates the locations list. */
export function useDeleteAddress() {
  const queryClient = useQueryClient();
  return useMutation({
    ...deleteLocationMutation(),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: getLocationsQueryKey() }),
  });
}
