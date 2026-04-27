export type LocationStatus = 'Active' | 'Inactive' | 'Completed';

export interface AddressRow {
  id: string;
  contact_name: string;
  address: string;
  delivery_group: string;
  notes: string;
  status: LocationStatus;
}
