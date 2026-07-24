import { useState } from 'react';

import { useAddresses } from '@/api/addresses';
import type {
  LocationRead,
  LocationStatusEnum,
} from '@/api/generated/types.gen';
import {
  getConfiguredDeliveryTypes,
  useSystemSettings,
} from '@/api/system-settings';
import type { UseSearchReturn } from '@/common/hooks';
import { useSearch } from '@/common/hooks';

export interface AddressesFilterState {
  statuses: Set<LocationStatusEnum>;
  deliveryTypes: Set<string>;
}

type SetElement<S> = S extends Set<infer V> ? V : never;

const emptyFilters = (): AddressesFilterState => ({
  statuses: new Set(),
  deliveryTypes: new Set(),
});

const copyFilters = (f: AddressesFilterState): AddressesFilterState => ({
  statuses: new Set(f.statuses),
  deliveryTypes: new Set(f.deliveryTypes),
});

export interface AddressesTabState {
  rows: LocationRead[];
  isLoading: boolean;
  deliveryTypes: string[];
  search: UseSearchReturn;
  filterOpen: boolean;
  setFilterOpen: (v: boolean) => void;
  appliedFilters: AddressesFilterState;
  draftFilters: AddressesFilterState;
  hasActiveFilters: boolean;
  openFilters: () => void;
  toggleDraft: <K extends keyof AddressesFilterState>(
    key: K,
    value: SetElement<AddressesFilterState[K]>
  ) => void;
  /** True when the draft has at least one chip selected (Clear All enabled). */
  draftHasSelections: boolean;
  /** Unselect every chip in the dialog; takes effect on Apply. */
  clearDraft: () => void;
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
  const deliveryTypes = getConfiguredDeliveryTypes(systemSettings);

  const hasActiveFilters = Object.values(appliedFilters).some(
    (s) => s.size > 0
  );

  // The filter chips hit the server (GET /locations accepts status and
  // delivery_type). Search has no backend param yet, so the search box is
  // still local-only UI.
  const { data, isLoading } = useAddresses({
    status:
      appliedFilters.statuses.size > 0
        ? [...appliedFilters.statuses]
        : undefined,
    delivery_type:
      appliedFilters.deliveryTypes.size > 0
        ? [...appliedFilters.deliveryTypes]
        : undefined,
  });
  // GET /locations is paginated; we currently surface only the first page.
  // Pagination controls (and a total count) are future work.
  const rows = data?.items ?? [];

  const openFilters = () => {
    setDraftFilters(copyFilters(appliedFilters));
    setFilterOpen(true);
  };

  const toggleDraft = <K extends keyof AddressesFilterState>(
    key: K,
    value: SetElement<AddressesFilterState[K]>
  ) => {
    setDraftFilters((prev) => {
      const next = new Set(prev[key]);
      if (next.has(value)) next.delete(value);
      else next.add(value);
      return { ...prev, [key]: next };
    });
  };

  const draftHasSelections = Object.values(draftFilters).some(
    (s) => s.size > 0
  );

  const clearDraft = () => setDraftFilters(emptyFilters());

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
    draftHasSelections,
    clearDraft,
    handleApply,
  };
}
