import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  getOrgContactOptions,
  getOrgContactQueryKey,
  getSystemSettingsOptions,
  getSystemSettingsQueryKey,
  patchSystemSettingsMutation,
} from './generated/@tanstack/react-query.gen';

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

export function useUpdateSystemSettings() {
  const queryClient = useQueryClient();
  return useMutation({
    ...patchSystemSettingsMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: getSystemSettingsQueryKey() });
      queryClient.invalidateQueries({ queryKey: getOrgContactQueryKey() });
    },
  });
}
