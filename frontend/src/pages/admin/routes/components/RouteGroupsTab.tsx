import { useMemo } from 'react';
import { Link } from 'react-router-dom';

import type { RouteGroupRead } from '@/api/generated/types.gen';
import type { Column } from '@/common/components';
import {
  Button,
  DataTable,
  HighlightText,
  Pagination,
  TableToolbar,
} from '@/common/components';
import { useRowHighlight, useTableSort } from '@/common/hooks';
import { orDash } from '@/common/utils';

import type { GroupsTabState } from '../hooks';
import { routeGroupDriveDateColumn } from './driveDateColumns';
import { EmptyState } from './EmptyState';
import { RouteFilterModal } from './RouteFilterModal';
import { RouteGroupActionsCell } from './RouteGroupActionsCell';
import { StatusHeader } from './StatusHeader';

const COLUMNS: Column<RouteGroupRead>[] = [
  { key: 'name', header: 'Name', render: (row) => row.name },
  routeGroupDriveDateColumn(),
  {
    key: 'delivery_type',
    header: 'Delivery Type',
    sortable: true,
    sortValue: (row) => row.delivery_type,
    // Null until the group has stops — its delivery type is whatever they are.
    render: (row) => orDash(row.delivery_type),
  },
  // Aggregate counts read '-' for groups with no routes yet (just created,
  // ahead of route generation)
  {
    key: 'num_routes',
    header: 'Routes',
    render: (row) => orDash(row.num_routes),
  },
  {
    key: 'num_locations',
    header: 'Locations',
    render: (row) => orDash(row.num_locations),
  },
  { key: 'num_boxes', header: 'Boxes', render: (row) => orDash(row.num_boxes) },
  {
    key: 'num_drivers_assigned',
    header: 'Drivers',
    render: (row) => orDash(row.num_drivers_assigned),
  },
  {
    key: 'status',
    sortable: true,
    sortValue: (row) => row.status,
    header: (
      <StatusHeader>
        <p>
          <span className="font-semibold">Upcoming:</span> Route is scheduled
          for the future
        </p>
        <p>
          <span className="font-semibold">Completed:</span> Route has been
          delivered
        </p>
      </StatusHeader>
    ),
    render: (row) => row.status,
  },
];

type RouteGroupsTabProps = GroupsTabState;

export function RouteGroupsTab({
  rows,
  page,
  setPage,
  totalPages,
  deliveryTypes,
  search,
  searchTerm,
  filterOpen,
  setFilterOpen,
  draftFilters,
  hasActiveFilters,
  openFilters,
  toggleDraft,
  draftHasSelections,
  clearDraft,
  handleApply,
}: RouteGroupsTabProps) {
  const { sort, toggleSort } = useTableSort();
  // Highlight + scroll for a row that was just added, duplicated, or re-dated.
  const { containerRef, highlightRow, getRowClassName } = useRowHighlight(rows);

  // The kebab lives inside the Status cell (the last column) rather than in
  // its own column: an extra column would compete for the table's leftover
  // width and either hoard it or squeeze the data columns. Status stretches
  // to the table edge already, so justify-between pins the kebab there while
  // the data columns keep their natural spread.
  const columns = useMemo<Column<RouteGroupRead>[]>(
    () =>
      COLUMNS.map((col) => {
        if (col.key === 'name') {
          return {
            ...col,
            // Placeholder link to the (not-yet-built) individual group page;
            // underlines on hover.
            render: (row: RouteGroupRead) => (
              <Link
                to={`/admin/routes/groups/${row.route_group_id}`}
                className="decoration-blue-300 hover:underline"
              >
                <HighlightText text={row.name} query={searchTerm} />
              </Link>
            ),
          };
        }
        if (col.key === 'drive_date') {
          return routeGroupDriveDateColumn(highlightRow);
        }
        if (col.key === 'status') {
          return {
            ...col,
            render: (row: RouteGroupRead) => (
              <div className="flex items-center justify-between gap-10">
                <span>{row.status}</span>
                <RouteGroupActionsCell row={row} onDuplicated={highlightRow} />
              </div>
            ),
          };
        }
        return col;
      }),
    [highlightRow, searchTerm]
  );

  return (
    <>
      <TableToolbar
        search={search}
        showFilter
        onFilterClick={openFilters}
        hasActiveFilters={hasActiveFilters}
        actions={
          <Button variant="primary" asChild>
            <Link to="/admin/routes/generation">Generate routes</Link>
          </Button>
        }
      />

      <div ref={containerRef}>
        <DataTable
          columns={columns}
          rows={rows}
          getRowKey={(r) => r.route_group_id}
          sort={sort}
          onSortChange={toggleSort}
          getRowClassName={(r) => getRowClassName(r.route_group_id)}
          emptyState={
            <EmptyState
              title="No route groups found"
              description="Try adjusting or clearing your filters"
            />
          }
        />
      </div>

      <Pagination page={page} totalPages={totalPages} onPageChange={setPage} />

      <RouteFilterModal
        open={filterOpen}
        onOpenChange={setFilterOpen}
        subtitle="Groups"
        deliveryTypes={deliveryTypes}
        draftFilters={draftFilters}
        toggleDraft={toggleDraft}
        draftHasSelections={draftHasSelections}
        clearDraft={clearDraft}
        handleApply={handleApply}
      />
    </>
  );
}
