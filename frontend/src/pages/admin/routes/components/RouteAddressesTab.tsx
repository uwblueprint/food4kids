import { useMemo } from 'react';

import type {
  LocationRead,
  LocationStatusEnum,
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
import { formatShortDate } from '@/common/utils';

import type { AddressesTabState } from '../hooks';
import { AddressActionsCell } from './AddressActionsCell';
import { EmptyState } from './EmptyState';

const STATUSES: LocationStatusEnum[] = ['Active', 'Unscheduled', 'Inactive'];

/** Renders a nullable/empty cell value as an em dash. */
const orDash = (value: string | null | undefined) =>
  value && value.length > 0 ? value : '—';

const COLUMNS: Column<LocationRead>[] = [
  {
    key: 'contact_name',
    header: 'Contact Name',
    render: (row) => row.contact_name,
  },
  { key: 'address', header: 'Address', render: (row) => row.address },
  {
    key: 'phone_primary',
    header: 'Phone Number',
    render: (row) => orDash(row.phone_primary),
  },
  {
    key: 'assigned_route',
    header: 'Assigned Route',
    render: (row) => orDash(row.assigned_route),
  },
  {
    key: 'delivery_group',
    header: 'Delivery Group',
    render: (row) => row.location_group_name,
  },
  {
    key: 'last_delivery',
    header: 'Last Delivery',
    render: (row) =>
      row.last_delivery_date ? formatShortDate(row.last_delivery_date) : '—',
  },
  {
    key: 'total_deliveries',
    header: 'Deliveries',
    render: (row) => row.total_deliveries,
  },
  {
    key: 'num_children',
    header: '# of Children',
    render: (row) => row.num_children,
  },
  {
    key: 'dietary_restrictions',
    header: 'Food Restrictions',
    render: (row) => orDash(row.dietary_restrictions),
  },
  { key: 'halal', header: 'Halal', render: (row) => (row.halal ? 'Y' : 'N') },
  {
    key: 'latest_note',
    header: 'Notes',
    render: (row) => orDash(row.latest_note),
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
              <span className="font-semibold">Active:</span> Scheduled on an
              upcoming route
            </p>
            <p>
              <span className="font-semibold">Unscheduled:</span> On the roster
              but not on an upcoming route
            </p>
            <p>
              <span className="font-semibold">Inactive:</span> Not on the
              current roster
            </p>
          </TooltipContent>
        </Tooltip>
      </span>
    ),
    render: (row) => row.status,
  },
];

type RouteAddressesTabProps = AddressesTabState;

export function RouteAddressesTab({
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
}: RouteAddressesTabProps) {
  // The kebab shares the Status cell (last column) so it doesn't compete for
  // table width — same treatment as the Groups and Routes tabs.
  const columns = useMemo<Column<LocationRead>[]>(
    () =>
      COLUMNS.map((col) =>
        col.key === 'status'
          ? {
              ...col,
              render: (row: LocationRead) => (
                <div className="flex items-center justify-between gap-10">
                  <span>{row.status}</span>
                  <AddressActionsCell row={row} />
                </div>
              ),
            }
          : col
      ),
    []
  );

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
          <Button variant="primary">Mark Inactive</Button>
          <Button variant="primary" shape="circular">
            <ShareIcon className="size-5" />
          </Button>
        </div>
      </div>

      <DataTable
        columns={columns}
        rows={rows}
        getRowKey={(r) => r.location_id}
        emptyState={
          <EmptyState
            title="No addresses found"
            description="Try adjusting your filters or generating new routes"
            image="boy-edge-case-with-questions"
          />
        }
      />

      <Modal open={filterOpen} onOpenChange={setFilterOpen}>
        <ModalContent>
          <ModalHeader>
            <ModalTitle>Filters</ModalTitle>
            <ModalDescription>Addresses</ModalDescription>
          </ModalHeader>

          <div className="flex flex-col gap-4">
            <FilterChipGroup label="Status">
              {STATUSES.map((status) => (
                <FilterChip
                  key={status}
                  selected={draftFilters.statuses.has(status)}
                  onClick={() => toggleDraft('statuses', status)}
                >
                  {status}
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
          </div>

          <ModalFooter className="mt-4">
            {/* Clear All only empties the dialog's chips; Apply persists them,
                which is also how an applied filter gets cleared. */}
            <Button
              variant="secondary"
              disabled={!draftHasSelections}
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
