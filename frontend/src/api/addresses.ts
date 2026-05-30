import { useQuery } from '@tanstack/react-query';

import { getLocationsOptions } from './generated/@tanstack/react-query.gen';

/**
 * Fetch the (paginated) list of locations for the admin routes "Addresses" tab.
 *
 * GET /locations has no search/filter params yet, so the tab's search box and
 * filter chips are local-only UI for now (see useAddressesTabState). Wiring
 * server-side search/filtering is tracked as future work.
 */
export function useAddresses() {
  return useQuery(getLocationsOptions());
}
