import { DataTable } from '@/common/components';
import type { Column } from '@/common/components';
import type { RouteGroupRow } from '@/types/route-group';

import { EmptyState } from './EmptyState';

const COLUMNS: Column<RouteGroupRow>[] = [];

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
