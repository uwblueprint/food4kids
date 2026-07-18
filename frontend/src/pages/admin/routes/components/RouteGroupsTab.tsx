import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';

import type {
  DriveDaysOfWeekEnum,
  DriverAssignmentStatusEnum,
  RouteGroupRead,
  RouteStatusEnum,
} from '@/api/generated/types.gen';
import FilterLinesIcon from '@/assets/icons/filter-lines.svg?react';
import InfoCircleIcon from '@/assets/icons/info-circle.svg?react';
import PlusIcon from '@/assets/icons/plus.svg?react';
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
import { cn } from '@/lib/utils';

import type { GroupsTabState } from '../hooks';
import { AddRouteGroupModal } from './AddRouteGroupModal';
import { DriveDateCell } from './DriveDateCell';
import { EmptyState } from './EmptyState';
import { RouteGroupActionsCell } from './RouteGroupActionsCell';

const WEEKDAYS: DriveDaysOfWeekEnum[] = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'];
// Archived is in the enum but group status is only ever computed as
// Upcoming/Completed, so the dialog doesn't offer it (matches the Figma).
const ROUTE_STATUSES: RouteStatusEnum[] = ['Upcoming', 'Completed'];
const DRIVER_STATUSES: DriverAssignmentStatusEnum[] = [
  'Assigned',
  'Unassigned',
];

const COLUMNS: Column<RouteGroupRead>[] = [
  { key: 'name', header: 'Name', render: (row) => row.name },
  {
    key: 'drive_date',
    header: 'Date',
    render: (row) => (
      <DriveDateCell
        routeGroupId={row.route_group_id}
        driveDate={row.drive_date}
      />
    ),
  },
  {
    key: 'delivery_type',
    header: 'Delivery Type',
    render: (row) => row.delivery_type,
  },
  // Aggregate counts read '-' for groups with no routes yet (just created,
  // ahead of route generation)
  {
    key: 'num_routes',
    header: 'Routes',
    render: (row) => row.num_routes || '-',
  },
  {
    key: 'num_locations',
    header: 'Locations',
    render: (row) => row.num_locations || '-',
  },
  { key: 'num_boxes', header: 'Boxes', render: (row) => row.num_boxes || '-' },
  {
    key: 'num_drivers_assigned',
    header: 'Drivers',
    render: (row) => row.num_drivers_assigned || '-',
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

/** How long a newly added group's row stays highlighted. */
const HIGHLIGHT_MS = 3000;

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
  draftHasSelections,
  clearDraft,
  handleApply,
}: RouteGroupsTabProps) {
  const [addOpen, setAddOpen] = useState(false);
  const [highlightedId, setHighlightedId] = useState<string | null>(null);
  const highlightTimer = useRef<ReturnType<typeof setTimeout> | undefined>(
    undefined
  );
  const tableWrapRef = useRef<HTMLDivElement>(null);
  const scrolledIdRef = useRef<string | null>(null);

  // Highlight + scroll for a newly added row — used by both the Add modal
  // and each row's Duplicate action.
  const handleCreated = useCallback((routeGroupId: string) => {
    clearTimeout(highlightTimer.current);
    scrolledIdRef.current = null;
    setHighlightedId(routeGroupId);
    highlightTimer.current = setTimeout(
      () => setHighlightedId(null),
      HIGHLIGHT_MS
    );
  }, []);

  // The kebab lives inside the Status cell (the last column) rather than in
  // its own column: an extra column would compete for the table's leftover
  // width and either hoard it or squeeze the data columns. Status stretches
  // to the table edge already, so justify-between pins the kebab there while
  // the data columns keep their natural spread.
  const columns = useMemo<Column<RouteGroupRead>[]>(
    () =>
      COLUMNS.map((col) =>
        col.key === 'status'
          ? {
              ...col,
              render: (row) => (
                <div className="flex items-center justify-between gap-10">
                  <span>{row.status}</span>
                  <RouteGroupActionsCell
                    row={row}
                    onDuplicated={handleCreated}
                  />
                </div>
              ),
            }
          : col
      ),
    [handleCreated]
  );

  // Scroll the just-added group into view once the refetched rows contain it.
  // Runs again as `rows` updates because the row doesn't exist in the DOM
  // until the list refetch lands; scrolledIdRef keeps it to one scroll per add.
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
          <Button
            variant="primary"
            shape="circular"
            aria-label="Add route group"
            onClick={() => setAddOpen(true)}
          >
            <PlusIcon className="size-5" />
          </Button>
        </div>
      </div>

      <div ref={tableWrapRef}>
        <DataTable
          columns={columns}
          rows={rows}
          getRowKey={(r) => r.route_group_id}
          getRowClassName={(r) =>
            cn(
              'transition-colors duration-500',
              r.route_group_id === highlightedId && 'bg-blue-50'
            )
          }
          emptyState={
            <EmptyState
              title="No routes yet"
              description="Try adjusting your filters or generating new routes"
            />
          }
        />
      </div>

      <AddRouteGroupModal
        open={addOpen}
        onOpenChange={setAddOpen}
        deliveryTypes={deliveryTypes}
        onCreated={handleCreated}
      />

      <Modal open={filterOpen} onOpenChange={setFilterOpen}>
        <ModalContent>
          <ModalHeader>
            <ModalTitle>Filters</ModalTitle>
            <ModalDescription>Groups</ModalDescription>
          </ModalHeader>

          <div className="flex flex-col gap-4">
            <FilterChipGroup label="Day">
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

            <FilterChipGroup label="Delivery Type">
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

            <FilterChipGroup label="Route Status">
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

            <FilterChipGroup label="Driver Status">
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

          <ModalFooter className="mt-4">
            {/* Clear All only empties the dialog's chips; Apply persists them,
                which is also how an applied filter gets cleared. */}
            <Button
              variant="secondary"
              disabled={!draftHasSelections}
              // The base button disables pointer events entirely; re-enable
              // them so the not-allowed cursor can show over the button.
              className="disabled:pointer-events-auto disabled:cursor-not-allowed"
              onClick={clearDraft}
            >
              Clear All
            </Button>
            <Button variant="primary" onClick={handleApply}>
              Apply
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  );
}
