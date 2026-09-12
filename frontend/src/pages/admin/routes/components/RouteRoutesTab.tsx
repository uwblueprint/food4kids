import { useCallback, useMemo } from 'react';
import { Link } from 'react-router-dom';

import type { RouteWithDateRead } from '@/api/generated/types.gen';
import type { Column } from '@/common/components';
import {
  Banner,
  Button,
  DataTable,
  HighlightText,
  Pagination,
  TableToolbar,
} from '@/common/components';
import { useRowHighlight, useTableSort } from '@/common/hooks';
import { orDash } from '@/common/utils';

import type { RoutesTabState } from '../hooks';
import { AssignDriverCell } from './AssignDriverCell';
import { routeDriveDateColumn } from './driveDateColumns';
import { EmptyState } from './EmptyState';
import { RouteActionsCell } from './RouteActionsCell';
import { RouteFilterModal } from './RouteFilterModal';
import { StatusHeader } from './StatusHeader';

const COLUMNS: Column<RouteWithDateRead>[] = [
  routeDriveDateColumn,
  {
    key: 'delivery_type',
    header: 'Delivery Type',
    sortable: true,
    sortValue: (row) => row.delivery_type,
    render: (row) => orDash(row.delivery_type),
  },
  { key: 'num_stops', header: 'Stops', render: (row) => row.num_stops },
  { key: 'box_total', header: 'Boxes', render: (row) => row.box_total },
  {
    key: 'length',
    header: 'Distance (km)',
    // One decimal on every row, as the design shows — a bare integer next to
    // "23.4" reads as a different quantity rather than a rounder one.
    render: (row) => row.length.toFixed(1),
  },
  {
    key: 'driver_name',
    header: 'Driver',
    render: (row) => row.driver_name ?? <AssignDriverCell row={row} />,
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

type RouteRoutesTabProps = RoutesTabState;

export function RouteRoutesTab({
  rows,
  page,
  setPage,
  totalPages,
  deliveryTypes,
  search,
  searchTerm,
  unassignedCount,
  bannerDismissed,
  dismissBanner,
  filterOpen,
  setFilterOpen,
  draftFilters,
  hasActiveFilters,
  openFilters,
  toggleDraft,
  draftHasSelections,
  clearDraft,
  handleApply,
}: RouteRoutesTabProps) {
  const { sort, toggleSort } = useTableSort();
  // Highlight + scroll a row after a driver reassignment updates it in place.
  const { containerRef, highlightRow, getRowClassName } = useRowHighlight(rows);
  const handleRowChanged = useCallback(
    (routeId: string) => highlightRow(routeId),
    [highlightRow]
  );

  const columns = useMemo<Column<RouteWithDateRead>[]>(
    () =>
      COLUMNS.map((col) => {
        if (col.key === 'driver_name') {
          return {
            ...col,
            render: (row: RouteWithDateRead) =>
              row.driver_name ? (
                <HighlightText text={row.driver_name} query={searchTerm} />
              ) : (
                <AssignDriverCell
                  row={row}
                  onUpdated={() => handleRowChanged(row.route_id)}
                />
              ),
          };
        }
        if (col.key === 'status') {
          return {
            ...col,
            // The kebab shares the Status cell (last column) so it doesn't
            // compete for table width — same treatment as the Groups tab.
            render: (row: RouteWithDateRead) => (
              <div className="flex items-center justify-between gap-10">
                <span>{row.status}</span>
                <RouteActionsCell
                  row={row}
                  onUpdated={() => handleRowChanged(row.route_id)}
                />
              </div>
            ),
          };
        }
        return col;
      }),
    [handleRowChanged, searchTerm]
  );

  return (
    <>
      {unassignedCount > 0 && !bannerDismissed && (
        <Banner variant="error" className="mb-6 py-4" onDismiss={dismissBanner}>
          <span className="text-red font-bold">{unassignedCount}</span> route
          {unassignedCount === 1 ? '' : 's'} missing assigned driver
          {unassignedCount === 1 ? '' : 's'}
        </Banner>
      )}

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
          getRowKey={(r) => r.route_id}
          sort={sort}
          onSortChange={toggleSort}
          getRowClassName={(r) => getRowClassName(r.route_id)}
          emptyState={
            <EmptyState
              title="No routes found"
              description="Try adjusting or clearing your filters"
            />
          }
        />
      </div>

      <Pagination page={page} totalPages={totalPages} onPageChange={setPage} />

      <RouteFilterModal
        open={filterOpen}
        onOpenChange={setFilterOpen}
        subtitle="Routes"
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
