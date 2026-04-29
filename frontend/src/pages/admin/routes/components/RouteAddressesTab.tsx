import FilterLinesIcon from '@/assets/icons/filter-lines.svg?react';
import {
  Button,
  DataTable,
  Modal,
  ModalContent,
  ModalDescription,
  ModalFooter,
  ModalHeader,
  ModalTitle,
  FilterChip,
  FilterChipGroup,
  SearchBar,
} from '@/common/components';
import type { Column } from '@/common/components';
import ShareIcon from '@/assets/icons/share.svg?react';

import type { AddressRow } from '@/types/address';

import type { AddressesTabState } from '../hooks';
import { EmptyState } from './EmptyState';

const ROUTE_STATUSES = ['Upcoming', 'Completed', 'Archived'];
const DELIVERY_TYPES = ['School Year', 'Summer'];

const COLUMNS: Column<AddressRow>[] = [
  {
    key: 'contact_name',
    header: 'School / Last Name',
    render: (row) => row.contact_name,
  },
  { key: 'address', header: 'Address', render: (row) => row.address },
  {
    key: 'delivery_group',
    header: 'Delivery Group',
    render: (row) => row.delivery_group,
  },
  { key: 'notes', header: 'Notes', render: (row) => row.notes },
  { key: 'status', header: 'Status', render: (row) => row.status },
];

interface RouteAddressesTabProps extends AddressesTabState {}

export function RouteAddressesTab({
  rows,
  search,
  filterOpen,
  setFilterOpen,
  draftFilters,
  hasActiveFilters,
  openFilters,
  toggleDraft,
  handleApply,
}: RouteAddressesTabProps) {
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
        columns={COLUMNS}
        rows={rows}
        getRowKey={(r) => r.id}
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
