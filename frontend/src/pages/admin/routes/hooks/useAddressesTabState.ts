import { useState } from 'react';

import { useAddresses } from '@/api/addresses';
import type { AddressRow } from '@/types/address';

export interface AddressesFilterState {
  routeStatuses: Set<string>;
  deliveryTypes: Set<string>;
}

const emptyFilters = (): AddressesFilterState => ({
  routeStatuses: new Set(),
  deliveryTypes: new Set(),
});

const copyFilters = (f: AddressesFilterState): AddressesFilterState => ({
  routeStatuses: new Set(f.routeStatuses),
  deliveryTypes: new Set(f.deliveryTypes),
});

export interface AddressesTabState {
  rows: AddressRow[];
  isLoading: boolean;
  search: string;
  setSearch: (v: string) => void;
  filterOpen: boolean;
  setFilterOpen: (v: boolean) => void;
  appliedFilters: AddressesFilterState;
  draftFilters: AddressesFilterState;
  hasActiveFilters: boolean;
  openFilters: () => void;
  toggleDraft: (key: keyof AddressesFilterState, value: string) => void;
  handleApply: () => void;
}

export function useAddressesTabState(): AddressesTabState {
  const [search, setSearch] = useState('');
  const [filterOpen, setFilterOpen] = useState(false);
  const [appliedFilters, setAppliedFilters] = useState<AddressesFilterState>(emptyFilters());
  const [draftFilters, setDraftFilters] = useState<AddressesFilterState>(emptyFilters());

  const hasActiveFilters = Object.values(appliedFilters).some((s) => s.size > 0);

  const { data: rows = [], isLoading } = useAddresses({
    search: search || undefined,
    routeStatuses: appliedFilters.routeStatuses.size > 0 ? [...appliedFilters.routeStatuses] : undefined,
    deliveryTypes: appliedFilters.deliveryTypes.size > 0 ? [...appliedFilters.deliveryTypes] : undefined,
  });

  const openFilters = () => {
    setDraftFilters(copyFilters(appliedFilters));
    setFilterOpen(true);
  };

  const toggleDraft = (key: keyof AddressesFilterState, value: string) => {
    setDraftFilters((prev) => {
      const next = new Set(prev[key]);
      if (next.has(value)) next.delete(value);
      else next.add(value);
      return { ...prev, [key]: next };
    });
  };

  const handleApply = () => {
    setAppliedFilters(copyFilters(draftFilters));
    setFilterOpen(false);
  };

  return {
    rows,
    isLoading,
    search,
    setSearch,
    filterOpen,
    setFilterOpen,
    appliedFilters,
    draftFilters,
    hasActiveFilters,
    openFilters,
    toggleDraft,
    handleApply,
  };
}
