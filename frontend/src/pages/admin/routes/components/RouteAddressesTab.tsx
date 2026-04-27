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

import type { AddressesTabState } from '../hooks';
import { EmptyState } from './EmptyState';

const ROUTE_STATUSES = ['Upcoming', 'Completed', 'Archived'];
const DELIVERY_TYPES = ['School Year', 'Summer'];

export type LocationStatus = 'Active' | 'Inactive' | 'Completed';

export interface AddressRow {
  id: string;
  contact_name: string;
  address: string;
  delivery_group: string;
  notes: string;
  status: LocationStatus;
}

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

// TODO: fetch data from API
interface RouteAddressesTabProps extends AddressesTabState {
  rows?: AddressRow[];
  actions?: ReactNode;
}

export function RouteAddressesTab({
  rows = [],
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
}: RouteAddressesTabProps) {
  return (
    <>
      <div className="mb-8 flex items-center justify-between">
        <div className="flex items-center gap-5">
          <SearchBar
            placeholder="Search anything"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            wrapperClassName="w-64"
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
            title="No addresses found"
            description="Try adjusting your filters or generating new routes"
            image="boy-edge-case-with-questions"
          />
        }
      />

      <Dialog open={filterOpen} onOpenChange={setFilterOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Filters</DialogTitle>
            <DialogDescription>Addresses</DialogDescription>
          </DialogHeader>

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
