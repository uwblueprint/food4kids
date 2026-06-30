import { useQuery } from '@tanstack/react-query';

import { getSystemSettingsOptions } from './generated/@tanstack/react-query.gen';
import type { SystemSettingsRead } from './generated/types.gen';

const DEFAULT_DELIVERY_TYPES = ['School', 'Family'];

export function getConfiguredDeliveryTypes(
  settings: SystemSettingsRead | null | undefined
) {
  return settings?.delivery_types && settings.delivery_types.length > 0
    ? settings.delivery_types
    : DEFAULT_DELIVERY_TYPES;
}

export function useSystemSettings() {
  return useQuery(getSystemSettingsOptions());
}
