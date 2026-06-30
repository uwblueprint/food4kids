import { useState } from 'react';

import { useAddresses } from '@/api/addresses';
import type { LocationReadOutput } from '@/api/generated/types.gen';
import { useSystemSettings } from '@/api/system-settings';
import type { UseSearchReturn } from '@/common/hooks';
import { useSearch } from '@/common/hooks';

const DEFAULT_DELIVERY_TYPES = ['School', 'Family'];

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
  rows: LocationReadOutput[];
  isLoading: boolean;
  deliveryTypes: string[];
  search: UseSearchReturn;
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
  const search = useSearch();
  const [filterOpen, setFilterOpen] = useState(false);
  const [appliedFilters, setAppliedFilters] =
    useState<AddressesFilterState>(emptyFilters());
  const [draftFilters, setDraftFilters] =
    useState<AddressesFilterState>(emptyFilters());
  const { data: systemSettings } = useSystemSettings();
  const deliveryTypes =
    systemSettings?.delivery_types && systemSettings.delivery_types.length > 0
      ? systemSettings.delivery_types
      : DEFAULT_DELIVERY_TYPES;

  const hasActiveFilters = Object.values(appliedFilters).some(
    (s) => s.size > 0
  );

  // NOTE: GET /locations has no search/filter params yet, so search and the
  // filter chips below are local-only UI for now (they don't reach the
  // backend). Wiring server-side search/filtering is tracked as future work.
  const { data, isLoading } = useAddresses();
  // GET /locations is paginated; we currently surface only the first page.
  // The tab is a WIP shell, so pagination controls (and a total count) are
  // future work alongside the server-side search/filtering above.
  const rows = data?.items ?? [];

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
    deliveryTypes,
    search,
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
