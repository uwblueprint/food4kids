import { useMutation } from '@tanstack/react-query';

import axiosClient from '@/lib/axiosClient';
import type { LocationImportResponse } from '@/types/location';

async function fetchValidateLocations(
  file: File,
  columnMap: Record<string, string>
): Promise<LocationImportResponse> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('column_map', JSON.stringify(columnMap));

  const response = await axiosClient.post<LocationImportResponse>(
    '/locations/validate',
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } }
  );
  return response.data;
}

export function useValidateLocations() {
  return useMutation({
    mutationFn: ({
      file,
      columnMap,
    }: {
      file: File;
      columnMap: Record<string, string>;
    }) => fetchValidateLocations(file, columnMap),
  });
}
