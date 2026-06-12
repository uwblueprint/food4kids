import { useQuery } from '@tanstack/react-query';

import { getSystemSettingsOptions } from './generated/@tanstack/react-query.gen';

export function useSystemSettings() {
  return useQuery(getSystemSettingsOptions());
}
