import { type ReactNode } from 'react';

import FilterLinesIcon from '@/assets/icons/filter-lines.svg?react';
import {
  Button,
  DataTable,
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  FilterChip,
  FilterChipGroup,
  SearchBar,
} from '@/common/components';
import type { Column } from '@/common/components';
import type { RouteGroupRow } from '@/types/route-group';

import type { GroupsTabState } from '../hooks';
import { EmptyState } from './EmptyState';

const WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'];
const DELIVERY_TYPES = ['School Year', 'Summer'];
const ROUTE_STATUSES = ['Upcoming', 'Completed', 'Archived'];
const DRIVER_STATUSES = ['Assigned', 'Unassigned'];

const COLUMNS: Column<RouteGroupRow>[] = [
  { key: 'name', header: 'Name', render: (row) => row.name },
  { key: 'date', header: 'Date', render: (row) => row.date },
  {
    key: 'delivery_type',
    header: 'Delivery Type',
    render: (row) => row.delivery_type,
  },
  { key: 'num_routes', header: '# of Routes', render: (row) => row.num_routes },
  {
    key: 'num_locations',
    header: 'Locations',
    render: (row) => row.num_locations,
  },
  { key: 'num_boxes', header: 'Boxes', render: (row) => row.num_boxes },
  {
    key: 'num_drivers_assigned',
    header: 'Drivers Assigned',
    render: (row) => row.num_drivers_assigned,
  },
  { key: 'status', header: 'Status', render: (row) => row.status },
];

interface RouteGroupsTabProps extends GroupsTabState {
  actions?: ReactNode;
}

export function RouteGroupsTab({
  rows,
  actions,
  search,
  setSearch,
  filterOpen,
  setFilterOpen,
  draftFilters,
  hasActiveFilters,
  openFilters,
  toggleDraft,
  handleApply,
}: RouteGroupsTabProps) {
  return (
    <>
      <div className="mb-8 flex items-center justify-between">
        <div className="flex items-center gap-5">
          <SearchBar
            placeholder="Search anything"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <Button
            variant="tertiary"
            shape="circular"
            className={hasActiveFilters ? 'bg-blue-50' : 'bg-white'}
            onClick={openFilters}
          >
            <FilterLinesIcon className="size-4" />
          </Button>
        </div>
        {actions && <div className="flex items-center gap-4">{actions}</div>}
      </div>

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

      <Dialog open={filterOpen} onOpenChange={setFilterOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Filters</DialogTitle>
            <DialogDescription>Routes</DialogDescription>
          </DialogHeader>

          <div className="flex flex-col gap-4">
            <FilterChipGroup label="Weekday">
              {WEEKDAYS.map((day) => (
                <FilterChip
                  key={day}
                  selected={draftFilters.weekdays.has(day)}
                  onClick={() => toggleDraft('weekdays', day)}
                >
                  {day}
                </FilterChip>
              ))}
            </FilterChipGroup>

            <FilterChipGroup label="Delivery Type" showDelimiter>
              {DELIVERY_TYPES.map((type) => (
                <FilterChip
                  key={type}
                  selected={draftFilters.deliveryTypes.has(type)}
                  onClick={() => toggleDraft('deliveryTypes', type)}
                >
                  {type}
                </FilterChip>
              ))}
            </FilterChipGroup>

            <FilterChipGroup label="Route Status" showDelimiter>
              {ROUTE_STATUSES.map((status) => (
                <FilterChip
                  key={status}
                  selected={draftFilters.routeStatuses.has(status)}
                  onClick={() => toggleDraft('routeStatuses', status)}
                >
                  {status}
                </FilterChip>
              ))}
            </FilterChipGroup>

            <FilterChipGroup label="Driver Status" showDelimiter>
              {DRIVER_STATUSES.map((status) => (
                <FilterChip
                  key={status}
                  selected={draftFilters.driverStatuses.has(status)}
                  onClick={() => toggleDraft('driverStatuses', status)}
                >
                  {status}
                </FilterChip>
              ))}
            </FilterChipGroup>
          </div>

          <DialogFooter>
            <Button variant="primary" onClick={handleApply}>
              Apply
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
