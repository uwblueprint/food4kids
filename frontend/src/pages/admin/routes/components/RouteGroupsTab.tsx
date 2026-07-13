import { Link } from 'react-router-dom';

import type {
  DriveDaysOfWeekEnum,
  DriverAssignmentStatusEnum,
  RouteGroupRead,
  RouteStatusEnum,
} from '@/api/generated/types.gen';
import FilterLinesIcon from '@/assets/icons/filter-lines.svg?react';
import InfoCircleIcon from '@/assets/icons/info-circle.svg?react';
import ShareIcon from '@/assets/icons/share.svg?react';
import type { Column } from '@/common/components';
import {
  Button,
  DataTable,
  FilterChip,
  FilterChipGroup,
  Modal,
  ModalContent,
  ModalDescription,
  ModalFooter,
  ModalHeader,
  ModalTitle,
  SearchBar,
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/common/components';

import type { GroupsTabState } from '../hooks';
import { EmptyState } from './EmptyState';

const WEEKDAYS: DriveDaysOfWeekEnum[] = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'];
const ROUTE_STATUSES: RouteStatusEnum[] = ['Upcoming', 'Completed', 'Archived'];
const DRIVER_STATUSES: DriverAssignmentStatusEnum[] = [
  'Assigned',
  'Unassigned',
];

const COLUMNS: Column<RouteGroupRead>[] = [
  { key: 'name', header: 'Name', render: (row) => row.name },
  { key: 'drive_date', header: 'Date', render: (row) => row.drive_date },
  {
    key: 'delivery_type',
    header: 'Delivery Type',
    render: (row) => row.delivery_type,
  },
  { key: 'num_routes', header: 'Routes', render: (row) => row.num_routes },
  {
    key: 'num_locations',
    header: 'Locations',
    render: (row) => row.num_locations,
  },
  { key: 'num_boxes', header: 'Boxes', render: (row) => row.num_boxes },
  {
    key: 'num_drivers_assigned',
    header: 'Drivers',
    render: (row) => row.num_drivers_assigned,
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

type RouteGroupsTabProps = GroupsTabState;

export function RouteGroupsTab({
  rows,
  deliveryTypes,
  search,
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
          <SearchBar placeholder="Search anything" {...search} />
          <Button
            variant="tertiary"
            shape="circular"
            className={hasActiveFilters ? 'bg-blue-50' : 'bg-white'}
            onClick={openFilters}
          >
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
        getRowKey={(r) => r.route_group_id}
        emptyState={
          <EmptyState
            title="No routes yet"
            description="Try adjusting your filters or generating new routes"
          />
        }
      />

      <Modal open={filterOpen} onOpenChange={setFilterOpen}>
        <ModalContent>
          <ModalHeader>
            <ModalTitle>Filters</ModalTitle>
            <ModalDescription>Routes</ModalDescription>
          </ModalHeader>

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
              {deliveryTypes.map((type) => (
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

          <ModalFooter>
            <Button variant="primary" onClick={handleApply}>
              Apply
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  );
}
