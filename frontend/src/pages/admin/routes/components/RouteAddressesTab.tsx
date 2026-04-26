import { DataTable } from '@/common/components';
import type { Column } from '@/common/components';

import { EmptyState } from './EmptyState';

// TODO: define AddressRow type in src/types/ when the addresses API is ready
interface AddressRow {
  id: string;
}

const COLUMNS: Column<AddressRow>[] = [
  // TODO: add address columns when the API is defined
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
