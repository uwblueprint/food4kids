import { useState } from 'react';

import { useAddresses } from '@/api/addresses';
import type {
  LocationRead,
  LocationStatusEnum,
} from '@/api/generated/types.gen';
import { useSystemSettings } from '@/api/system-settings';
import type { UsePaginationReturn, UseSearchReturn } from '@/common/hooks';
import {
  clampPage,
  TABLE_PAGE_SIZE,
  useDebouncedValue,
  usePagination,
  useSearch,
} from '@/common/hooks';

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

export interface AddressesTabState extends UsePaginationReturn {
  rows: LocationRead[];
  isLoading: boolean;
  totalPages: number;
  deliveryTypes: string[];
  search: UseSearchReturn;
  /** Debounced search term the rows were filtered by, for highlighting. */
  searchTerm: string;
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
  // Empty until settings load; the filter dialog hides the group either way.
  const deliveryTypes = systemSettings?.delivery_types ?? [];

  const hasActiveFilters = Object.values(appliedFilters).some(
    (s) => s.size > 0
  );

  // Filters and search all hit the server (GET /locations accepts status,
  // delivery_type, and a case-insensitive address/postal search). Debounced so
  // the query fires once typing pauses.
  const debouncedSearch = useDebouncedValue(search.value);

  const query = {
    search: debouncedSearch.trim() || undefined,
    status:
      appliedFilters.statuses.size > 0
        ? [...appliedFilters.statuses]
        : undefined,
    delivery_type:
      appliedFilters.deliveryTypes.size > 0
        ? [...appliedFilters.deliveryTypes]
        : undefined,
  };
  const { page, setPage } = usePagination(JSON.stringify(query));

  const { data, isLoading } = useAddresses({
    ...query,
    page,
    page_size: TABLE_PAGE_SIZE,
  });

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

  const totalPages = data?.total_pages ?? 0;

  return {
    rows: data?.items ?? [],
    isLoading,
    page: clampPage(page, totalPages, setPage),
    setPage,
    totalPages,
    deliveryTypes,
    search,
    searchTerm: debouncedSearch.trim(),
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
