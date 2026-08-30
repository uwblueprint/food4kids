import { useCallback, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

import type { RouteWithDateRead } from '@/api/generated/types.gen';
import { useRoutes } from '@/api/routes';
import type { Column } from '@/common/components';
import {
  Banner,
  Button,
  DataTable,
  HighlightText,
  Pagination,
  TableToolbar,
} from '@/common/components';
import {
  clampPage,
  TABLE_PAGE_SIZE,
  useDebouncedValue,
  usePagination,
  useRowHighlight,
  useSearch,
  useTableSort,
} from '@/common/hooks';
import { orDash, parseDateOnly } from '@/common/utils';

import { routeFiltersToQuery, useRouteFilters } from '../hooks';
import { AssignDriverCell } from './AssignDriverCell';
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

export function RouteRoutesTab() {
  const search = useSearch();
  // Debounced so the driver-name search hits the server once typing pauses.
  const searchTerm = useDebouncedValue(search.value).trim();
  const filters = useRouteFilters();
  const query = {
    search: searchTerm || undefined,
    ...routeFiltersToQuery(filters.appliedFilters),
  };
  const { page: requestedPage, setPage } = usePagination(JSON.stringify(query));
  const { data } = useRoutes({
    ...query,
    page: requestedPage,
    page_size: TABLE_PAGE_SIZE,
  });
  const rows = useMemo(() => data?.items ?? [], [data]);
  const totalPages = data?.total_pages ?? 0;
  const page = clampPage(requestedPage, totalPages, setPage);
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
        sortValue: (row: RouteWithDateRead) => parseDateOnly(row.drive_date),
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
    ],
    [handleRowChanged, searchTerm]
  );

  // Counted server-side rather than from `rows`: the banner is about the whole
  // filtered result set and `rows` is one page of it. page_size 1 because only
  // the total is wanted — the item itself is thrown away. The driver-assignment
  // chip is deliberately overridden: the banner answers "how many routes still
  // need a driver", which is the same question whichever side of that filter
  // you are currently looking at.
  const { data: unassigned } = useRoutes({
    ...query,
    driver_assignment_status: ['Unassigned'],
    page_size: 1,
  });
  const unassignedCount = unassigned?.total ?? 0;

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
