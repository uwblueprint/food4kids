import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';

import type { RouteWithDateRead } from '@/api/generated/types.gen';
import { useRoutes } from '@/api/routes';
import FilterLinesIcon from '@/assets/icons/filter-lines.svg?react';
import InfoCircleIcon from '@/assets/icons/info-circle.svg?react';
import ShareIcon from '@/assets/icons/share.svg?react';
import type { Column } from '@/common/components';
import {
  Button,
  DataTable,
  SearchBar,
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/common/components';
import { useSearch } from '@/common/hooks';
import { cn } from '@/lib/utils';

import { DriveDateCell } from './DriveDateCell';
import { EmptyState } from './EmptyState';
import { RouteActionsCell } from './RouteActionsCell';

const COLUMNS: Column<RouteWithDateRead>[] = [
  {
    key: 'delivery_type',
    header: 'Delivery Type',
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
    render: (row) => row.driver_name ?? '—',
  },
  {
    key: 'status',
    header: (
      <span className="flex items-center gap-1.5">
        Status
        <Tooltip>
          <TooltipTrigger asChild>
            <InfoCircleIcon className="size-4 cursor-pointer" />
          </TooltipTrigger>
          <TooltipContent>
            <p>
              <span className="font-semibold">Upcoming:</span> Route is
              scheduled for the future
            </p>
            <p>
              <span className="font-semibold">Completed:</span> Route has been
              delivered
            </p>
          </TooltipContent>
        </Tooltip>
      </span>
    ),
    render: (row) => row.status,
  },
];

/** How long a re-dated route's row stays highlighted. */
const HIGHLIGHT_MS = 3000;

export function RouteRoutesTab() {
  const search = useSearch();
  const { data } = useRoutes();
  const rows = useMemo(() => data?.items ?? [], [data]);
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
        render: (row) => (
          <DriveDateCell
            routeGroupId={row.route_group_id}
            driveDate={row.drive_date}
            onUpdated={() => handleRowChanged(row.route_id)}
          />
        ),
      },
      ...COLUMNS.map((col) =>
        col.key === 'status'
          ? {
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
            }
          : col
      ),
    ],
    [handleRowChanged]
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
          getRowClassName={(r) =>
            cn(
              'transition-colors duration-500',
              r.route_id === highlightedId && 'bg-blue-50'
            )
          }
          emptyState={
            <EmptyState
              title="No routes found"
              description="Try adjusting or clearing your filters"
            />
          }
        />
      </div>
    </>
  );
}
