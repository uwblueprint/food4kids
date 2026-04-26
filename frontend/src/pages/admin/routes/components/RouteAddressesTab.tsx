import { DataTable } from '@/common/components';
import type { Column } from '@/common/components';

import { EmptyState } from './EmptyState';

export type LocationStatus = 'Active' | 'Inactive' | 'Completed';

export interface AddressRow {
  id: string;
  contact_name: string;
  address: string;
  delivery_group: string;
  notes: string;
  status: LocationStatus;
}

const COLUMNS: Column<AddressRow>[] = [
  {
    key: 'contact_name',
    header: 'School / Last Name',
    render: (row) => row.contact_name,
  },
  {
    key: 'address',
    header: 'Address',
    render: (row) => row.address,
  },
  {
    key: 'delivery_group',
    header: 'Delivery Group',
    render: (row) => row.delivery_group,
  },
  {
    key: 'notes',
    header: 'Notes',
    render: (row) => row.notes,
  },
  {
    key: 'status',
    header: 'Status',
    render: (row) => row.status,
  },
];

interface RouteAddressesTabProps {
  rows?: AddressRow[];
}

export function RouteAddressesTab({ rows = [] }: RouteAddressesTabProps) {
  return (
    <DataTable
      columns={COLUMNS}
      rows={rows}
      getRowKey={(r) => r.id}
      emptyState={
        <EmptyState
          title="No addresses found"
          description="Try adjusting your filters or generating new routes"
          image="boy-edge-case-with-questions"
        />
      }
    />
  );
}
