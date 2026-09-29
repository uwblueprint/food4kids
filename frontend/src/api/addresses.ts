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
 * The status and delivery_type filters and the `search` box all reach the
 * server; `search` matches (case-insensitively) every text column the table
 * shows, plus the phone numbers by digits.
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
