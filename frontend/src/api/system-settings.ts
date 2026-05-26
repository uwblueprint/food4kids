import { useQuery } from '@tanstack/react-query';

import axiosClient from '@/lib/axiosClient';

export interface SystemSettings {
  system_settings_id: string;
  default_cap: number | null;
  route_start_time: string | null;
  warehouse_location: string | null;
  warehouse_longitude: number | null;
  warehouse_latitude: number | null;
  import_column_map: Record<string, string> | null;
}

async function fetchSystemSettings(): Promise<SystemSettings | null> {
  const response = await axiosClient.get<SystemSettings | null>(
    '/system-settings/'
  );
  return response.data;
}

export function useSystemSettings() {
  return useQuery({
    queryKey: ['system-settings'],
    queryFn: fetchSystemSettings,
  });
}
