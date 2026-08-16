import { useQuery } from '@tanstack/react-query';

import {
  getOrgContactOptions,
  getSystemSettingsOptions,
} from './generated/@tanstack/react-query.gen';
import type { SystemSettingsRead } from './generated/types.gen';

export function getConfiguredDeliveryTypes(
  settings: SystemSettingsRead | null | undefined
) {
  return settings?.delivery_types ?? [];
}

export function useSystemSettings() {
  return useQuery(getSystemSettingsOptions());
}

/**
 * The org's point of contact — the name and number Settings calls "the number
 * the Call Food4Kids button leads to".
 *
 * A separate query from {@link useSystemSettings} because the endpoint behind
 * it is unauthenticated: the two screens that need it are the driver route
 * view (a driver, not an admin) and the catch-all error page, which renders
 * for logged-out visitors. `useSystemSettings` would 401 for both.
 *
 * `contact_phone` arrives as RFC 3966 (`tel:+1-519-576-3443;ext=1`), i.e.
 * already a valid `href` — pass it through untouched for links, and through
 * `formatPhone` for anything the reader sees.
 */
export function useOrgContact() {
  return useQuery(getOrgContactOptions());
}
