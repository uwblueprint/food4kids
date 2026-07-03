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

import { EmptyState } from './EmptyState';

const COLUMNS: Column<RouteWithDateRead>[] = [
  {
    key: 'drive_date',
    header: 'Delivery Date',
    render: (row) =>
      new Date(row.drive_date).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      }),
  },
  {
    key: 'delivery_type',
    header: 'Delivery Type',
    render: () => '—',
  },
  { key: 'num_stops', header: 'Stops', render: (row) => row.num_stops },
  { key: 'box_total', header: 'Boxes', render: (row) => row.box_total },
  {
    key: 'length',
    header: 'Distance (km)',
    render: (row) => row.length,
  },
  { key: 'driver', header: 'Driver', render: () => '—' },
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
    render: () => '—',
  },
];

export function RouteRoutesTab() {
  const search = useSearch();
  const { data } = useRoutes();
  const rows = data?.items ?? [];

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

      <DataTable
        columns={COLUMNS}
        rows={rows}
        getRowKey={(r) => r.route_id}
        emptyState={
          <EmptyState
            title="No routes found"
            description="Try adjusting or clearing your filters"
          />
        }
      />
    </>
  );
}
