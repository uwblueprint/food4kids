import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';

import type { RouteWithDateRead } from '@/api/generated/types.gen';
import { useRoutes } from '@/api/routes';
import AlertCircleIcon from '@/assets/icons/alert-circle.svg?react';
import FilterLinesIcon from '@/assets/icons/filter-lines.svg?react';
import ShareIcon from '@/assets/icons/share.svg?react';
import type { Column } from '@/common/components';
import {
  Banner,
  Button,
  DataTable,
  HighlightText,
  SearchBar,
} from '@/common/components';
import { useDebouncedValue, useSearch, useTableSort } from '@/common/hooks';
import { cn } from '@/lib/utils';

import { DriveDateCell } from './DriveDateCell';
import { EmptyState } from './EmptyState';
import { RouteActionsCell } from './RouteActionsCell';
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

/** How long a re-dated route's row stays highlighted. */
const HIGHLIGHT_MS = 3000;

export function RouteRoutesTab() {
  const search = useSearch();
  // Debounced so the driver-name search hits the server once typing pauses.
  const searchTerm = useDebouncedValue(search.value).trim();
  const { data } = useRoutes({ search: searchTerm || undefined });
  const rows = useMemo(() => data?.items ?? [], [data]);
  const { sort, toggleSort } = useTableSort();
  const [bannerDismissed, setBannerDismissed] = useState(false);
  const [highlightedId, setHighlightedId] = useState<string | null>(null);
  const highlightTimer = useRef<ReturnType<typeof setTimeout> | undefined>(
    undefined
  );
  const tableWrapRef = useRef<HTMLDivElement>(null);
  const scrolledIdRef = useRef<string | null>(null);

  // Highlight and scroll to a row after it changes (date edits re-sort it,
  // driver reassignments update it in place) — same treatment as Groups.
  const handleRowChanged = useCallback((routeId: string) => {
    clearTimeout(highlightTimer.current);
    scrolledIdRef.current = null;
    setHighlightedId(routeId);
    highlightTimer.current = setTimeout(
      () => setHighlightedId(null),
      HIGHLIGHT_MS
    );
  }, []);

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

  // Scroll the re-dated route into view once the refetched rows place it.
  // Runs again as `rows` updates because the row may re-sort after the list
  // refetch lands; scrolledIdRef keeps it to one scroll per change.
  useEffect(() => {
    if (!highlightedId || scrolledIdRef.current === highlightedId) return;
    const row = tableWrapRef.current?.querySelector(
      `[data-row-key="${highlightedId}"]`
    );
    if (row) {
      scrolledIdRef.current = highlightedId;
      row.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, [highlightedId, rows]);

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

      <div className="mb-8 flex items-center justify-between">
        <div className="flex items-center gap-5">
          <SearchBar placeholder="Search anything" {...search} />
          <Button variant="tertiary" shape="circular">
            <FilterLinesIcon className="size-4" />
          </Button>
        </div>
        <div className="flex items-center gap-4">
          <Button variant="primary" asChild>
            <Link to="/admin/routes/generation">Generate Routes</Link>
          </Button>
          <Button variant="primary" shape="circular">
            <ShareIcon className="size-5" />
          </Button>
        </div>
      </div>

      <div ref={tableWrapRef}>
        <DataTable
          columns={columns}
          rows={rows}
          getRowKey={(r) => r.route_id}
          sort={sort}
          onSortChange={toggleSort}
          getRowClassName={(r) =>
            cn(
              'transition-colors duration-500',
              r.route_id === highlightedId && 'bg-blue-50'
            )
          }
          emptyState={
            <EmptyState
              title="No routes found"
              description="Try adjusting your filters or generating new routes"
            />
          }
        />
      </div>
    </>
  );
}
