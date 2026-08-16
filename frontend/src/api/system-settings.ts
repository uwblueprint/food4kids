import { useQuery } from '@tanstack/react-query';

import {
  getOrgContactOptions,
  getSystemSettingsOptions,
} from './generated/@tanstack/react-query.gen';
import type { SystemSettingsRead } from './generated/types.gen';

// `undefined` only — while the query is in flight. The API no longer answers
// null: a missing settings row is a broken deployment and fails the request.
export function getConfiguredDeliveryTypes(
  settings: SystemSettingsRead | undefined
) {
  return settings?.delivery_types ?? [];
}

export function useSystemSettings() {
  return useQuery(getSystemSettingsOptions());
}

/**
 * The org's point of contact. Separate from {@link useSystemSettings} because
 * its endpoint is unauthenticated — that one would 401 for both callers.
 *
 * `contact_phone` is RFC 3966, i.e. already a valid `href`. Pass it through
 * untouched for links, and through `formatPhone` for anything a reader sees.
 */
export function useOrgContact() {
  return useQuery(getOrgContactOptions());
}
