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

// ---------------------------------------------------------------------------
// Review Changes
// ---------------------------------------------------------------------------

export interface NetNewEntry {
  row: number;
  contact_name: string;
  address: string;
  delivery_group: string | null;
  phone_number: string;
  num_boxes: number | null;
}

export interface StaleEntry {
  location_id: string;
  contact_name: string;
  address: string;
  delivery_group: string | null;
  phone_number: string;
}

/** A field that has changed: carries both the incoming and existing value. */
export interface ChangedField<T> {
  new_value: T;
  old_value: T;
}

/** Each field is either unchanged (plain value) or a ChangedField. */
export interface ChangedEntry {
  contact_name: string;
  address: string | ChangedField<string>;
  delivery_group: string | null | ChangedField<string | null>;
  phone_number: string | ChangedField<string>;
  num_children: number | null | ChangedField<number | null>;
}

export interface ReviewChangesResponse {
  net_new: NetNewEntry[];
  stale: StaleEntry[];
  changed: ChangedEntry[];
}
