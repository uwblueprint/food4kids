import { useState } from 'react';

export interface GroupsFilterState {
  weekdays: Set<string>;
  deliveryTypes: Set<string>;
  routeStatuses: Set<string>;
  driverStatuses: Set<string>;
}

const emptyFilters = (): GroupsFilterState => ({
  weekdays: new Set(),
  deliveryTypes: new Set(),
  routeStatuses: new Set(),
  driverStatuses: new Set(),
});

const copyFilters = (f: GroupsFilterState): GroupsFilterState => ({
  weekdays: new Set(f.weekdays),
  deliveryTypes: new Set(f.deliveryTypes),
  routeStatuses: new Set(f.routeStatuses),
  driverStatuses: new Set(f.driverStatuses),
});

export interface GroupsTabState {
  search: string;
  setSearch: (v: string) => void;
  filterOpen: boolean;
  setFilterOpen: (v: boolean) => void;
  appliedFilters: GroupsFilterState;
  draftFilters: GroupsFilterState;
  hasActiveFilters: boolean;
  openFilters: () => void;
  toggleDraft: (key: keyof GroupsFilterState, value: string) => void;
  handleApply: () => void;
}

export function useGroupsTabState(): GroupsTabState {
  const [search, setSearch] = useState('');
  const [filterOpen, setFilterOpen] = useState(false);
  const [appliedFilters, setAppliedFilters] = useState<GroupsFilterState>(emptyFilters());
  const [draftFilters, setDraftFilters] = useState<GroupsFilterState>(emptyFilters());

  const hasActiveFilters = Object.values(appliedFilters).some((s) => s.size > 0);

  const openFilters = () => {
    setDraftFilters(copyFilters(appliedFilters));
    setFilterOpen(true);
  };

  const toggleDraft = (key: keyof GroupsFilterState, value: string) => {
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
    // TODO: pass appliedFilters to data fetching logic
  };

  return {
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
