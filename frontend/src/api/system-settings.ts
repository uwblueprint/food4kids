import { useQuery } from '@tanstack/react-query';

import { getSystemSettingsOptions } from './generated/@tanstack/react-query.gen';
import type { SystemSettingsRead } from './generated/types.gen';

export function getConfiguredDeliveryTypes(
  settings: SystemSettingsRead | null | undefined
) {
  return settings?.delivery_types ?? [];
}

export function useSystemSettings() {
  return useQuery(getSystemSettingsOptions());
}
