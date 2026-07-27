import { useCallback, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

import type { RouteWithDateRead } from '@/api/generated/types.gen';
import { useRoutes } from '@/api/routes';
import AlertCircleIcon from '@/assets/icons/alert-circle.svg?react';
import type { Column } from '@/common/components';
import {
  Banner,
  Button,
  DataTable,
  HighlightText,
  TableToolbar,
} from '@/common/components';
import {
  useDebouncedValue,
  useRowHighlight,
  useSearch,
  useTableSort,
} from '@/common/hooks';

import { routeFiltersToQuery, useRouteFilters } from '../hooks';
import { DriveDateCell } from './DriveDateCell';
import { EmptyState } from './EmptyState';
import { RouteActionsCell } from './RouteActionsCell';
import { RouteFilterModal } from './RouteFilterModal';
import { StatusHeader } from './StatusHeader';

const COLUMNS: Column<RouteWithDateRead>[] = [
  {
    key: 'delivery_type',
    header: 'Delivery Type',
    sortable: true,
    sortValue: (row) => row.delivery_type,
    render: (row) => row.delivery_type ?? '—',
  },
  { key: 'num_stops', header: 'Stops', render: (row) => row.num_stops },
  { key: 'box_total', header: 'Boxes', render: (row) => row.box_total },
  {
    key: 'length',
    header: 'Distance (km)',
    render: (row) => row.length,
  },
  {
    key: 'driver_name',
    header: 'Driver',
    render: (row) =>
      row.driver_name ?? (
        <span className="flex items-center gap-2">
          <AlertCircleIcon className="text-red size-4 shrink-0" />
          Unassigned
        </span>
      ),
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

export function RouteRoutesTab() {
  const search = useSearch();
  // Debounced so the driver-name search hits the server once typing pauses.
  const searchTerm = useDebouncedValue(search.value).trim();
  const filters = useRouteFilters();
  const { data } = useRoutes({
    search: searchTerm || undefined,
    ...routeFiltersToQuery(filters.appliedFilters),
  });
  const rows = useMemo(() => data?.items ?? [], [data]);
  const { sort, toggleSort } = useTableSort();
  const [bannerDismissed, setBannerDismissed] = useState(false);
  // Highlight + scroll a row after a date edit (re-sorts it) or a driver
  // reassignment (updates it in place).
  const { containerRef, highlightRow, getRowClassName } = useRowHighlight(rows);
  const handleRowChanged = useCallback(
    (routeId: string) => highlightRow(routeId),
    [highlightRow]
  );

  const columns = useMemo<Column<RouteWithDateRead>[]>(
    () => [
      {
        key: 'drive_date',
        header: 'Delivery Date',
        sortable: true,
        sortValue: (row: RouteWithDateRead) => new Date(row.drive_date),
        render: (row) => (
          <DriveDateCell
            routeGroupId={row.route_group_id}
            driveDate={row.drive_date}
            onUpdated={() => handleRowChanged(row.route_id)}
          />
        ),
      },
      ...COLUMNS.map((col) => {
        if (col.key === 'driver_name') {
          return {
            ...col,
            render: (row: RouteWithDateRead) =>
              row.driver_name ? (
                <HighlightText text={row.driver_name} query={searchTerm} />
              ) : (
                <span className="flex items-center gap-2">
                  <AlertCircleIcon className="text-red size-4 shrink-0" />
                  Unassigned
                </span>
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
    ],
    [handleRowChanged, searchTerm]
  );

  const unassignedCount = useMemo(
    () => rows.filter((r) => !r.driver_name).length,
    [rows]
  );

  return (
    <>
      {unassignedCount > 0 && !bannerDismissed && (
        <Banner
          variant="error"
          className="mb-6 py-4"
          onDismiss={() => setBannerDismissed(true)}
        >
          <span className="text-red font-bold">{unassignedCount}</span> route
          {unassignedCount === 1 ? '' : 's'} missing assigned driver
          {unassignedCount === 1 ? '' : 's'}
        </Banner>
      )}

      <TableToolbar
        search={search}
        showFilter
        onFilterClick={filters.openFilters}
        hasActiveFilters={filters.hasActiveFilters}
        actions={
          <Button variant="primary" asChild>
            <Link to="/admin/routes/generation">Generate Routes</Link>
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
              description="Try adjusting your filters or generating new routes"
            />
          }
        />
      </div>

      <RouteFilterModal
        open={filters.filterOpen}
        onOpenChange={filters.setFilterOpen}
        subtitle="Routes"
        deliveryTypes={filters.deliveryTypes}
        draftFilters={filters.draftFilters}
        toggleDraft={filters.toggleDraft}
        draftHasSelections={filters.draftHasSelections}
        clearDraft={filters.clearDraft}
        handleApply={filters.handleApply}
      />
    </>
  );
}
