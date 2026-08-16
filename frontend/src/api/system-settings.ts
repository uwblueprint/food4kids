import { useQuery } from '@tanstack/react-query';

import {
  getOrgContactOptions,
  getSystemSettingsOptions,
} from './generated/@tanstack/react-query.gen';
import type { SystemSettingsRead } from './generated/types.gen';

// `undefined` only — the in-flight state. The API no longer answers null.
export function getConfiguredDeliveryTypes(
  settings: SystemSettingsRead | undefined
) {
  return settings?.delivery_types ?? [];
}

export function useSystemSettings() {
  return useQuery(getSystemSettingsOptions());
}

/**
 * The org's name and phone, from the public endpoint — {@link useSystemSettings}
 * would 401 for driver screens and the error page.
 *
 * `contact_phone` is RFC 3966: already a valid `href`, use `formatPhone` to
 * display it.
 */
export function useOrgContact() {
  return useQuery(getOrgContactOptions());
}
