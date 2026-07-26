import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

import type {
  DriveDaysOfWeekEnum,
  DriverAssignmentStatusEnum,
  RouteGroupRead,
  RouteStatusEnum,
} from '@/api/generated/types.gen';
import PlusIcon from '@/assets/icons/plus.svg?react';
import type { Column } from '@/common/components';
import {
  Button,
  DataTable,
  FilterChip,
  FilterChipGroup,
  HighlightText,
  Modal,
  ModalContent,
  ModalDescription,
  ModalFooter,
  ModalHeader,
  ModalTitle,
  TableToolbar,
} from '@/common/components';
import { useRowHighlight, useTableSort } from '@/common/hooks';

import type { GroupsTabState } from '../hooks';
import { AddRouteGroupModal } from './AddRouteGroupModal';
import { DriveDateCell } from './DriveDateCell';
import { EmptyState } from './EmptyState';
import { RouteGroupActionsCell } from './RouteGroupActionsCell';
import { StatusHeader } from './StatusHeader';

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
    sortable: true,
    sortValue: (row) => new Date(row.drive_date),
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
    sortable: true,
    sortValue: (row) => row.delivery_type,
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
  const [addOpen, setAddOpen] = useState(false);
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
          return {
            ...col,
            render: (row: RouteGroupRead) => (
              <DriveDateCell
                routeGroupId={row.route_group_id}
                driveDate={row.drive_date}
                onUpdated={() => highlightRow(row.route_group_id)}
              />
            ),
          };
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
          <>
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
          </>
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
              title="No routes found"
              description="Try adjusting your filters or generating new routes"
            />
          }
        />
      </div>

      <AddRouteGroupModal
        open={addOpen}
        onOpenChange={setAddOpen}
        deliveryTypes={deliveryTypes}
        onCreated={highlightRow}
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
