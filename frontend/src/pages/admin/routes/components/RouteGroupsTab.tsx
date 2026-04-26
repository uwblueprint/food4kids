import { DataTable } from '@/common/components';
import type { Column } from '@/common/components';
import type { RouteGroupRow } from '@/types/route-group';

import { EmptyState } from './EmptyState';

const COLUMNS: Column<RouteGroupRow>[] = [
  {
    key: 'name',
    header: 'Name',
    render: (row) => row.name,
  },
  {
    key: 'date',
    header: 'Date',
    render: (row) => row.date,
  },
  {
    key: 'delivery_type',
    header: 'Delivery Type',
    render: (row) => row.delivery_type,
  },
  {
    key: 'num_routes',
    header: '# of Routes',
    render: (row) => row.num_routes,
  },
  {
    key: 'num_locations',
    header: 'Locations',
    render: (row) => row.num_locations,
  },
  {
    key: 'num_boxes',
    header: 'Boxes',
    render: (row) => row.num_boxes,
  },
  {
    key: 'num_drivers_assigned',
    header: 'Drivers Assigned',
    render: (row) => row.num_drivers_assigned,
  },
  {
    key: 'status',
    header: 'Status',
    render: (row) => row.status,
  },
];

interface RouteGroupsTabProps {
  rows?: RouteGroupRow[];
}

export function RouteGroupsTab({ rows = [] }: RouteGroupsTabProps) {
  return (
    <DataTable
      columns={COLUMNS}
      rows={rows}
      getRowKey={(r) => r.id}
      emptyState={
        <EmptyState
          title="No routes yet"
          description="Try adjusting your filters or generating new routes"
        />
      }
    />
  );
}
