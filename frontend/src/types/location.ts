export type AlertCode =
  | 'MISSING_FIELDS'
  | 'INVALID_FORMAT'
  | 'LOCAL_DUPLICATE'
  | 'MISSING_DELIVERY_GROUP'
  | 'PARTIAL_DUPLICATE';

export interface LocationImportEntry {
  contact_name: string | null;
  address: string | null;
  delivery_group: string | null;
  phone_number: string | null;
  num_boxes: number | null;
  halal: boolean | null;
  dietary_restrictions: string | null;
}

export interface LocationImportRow {
  row: number;
  location: LocationImportEntry;
  alerts: AlertCode[];
}

export interface LocationImportResponse {
  success: boolean;
  total_rows: number;
  rows: LocationImportRow[];
}
