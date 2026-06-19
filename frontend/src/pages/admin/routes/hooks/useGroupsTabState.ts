import { useState } from 'react';

import type {
  DeliveryTypeEnum,
  DriveDaysOfWeekEnum,
  DriverAssignmentStatusEnum,
  RouteGroupRead,
  RouteStatusEnum,
} from '@/api/generated/types.gen';
import { useRouteGroups } from '@/api/route-groups';
import type { UseSearchReturn } from '@/common/hooks';
import { useSearch } from '@/common/hooks';

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
  rows: RouteGroupRead[];
  isLoading: boolean;
  search: UseSearchReturn;
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
  const search = useSearch();
  const [filterOpen, setFilterOpen] = useState(false);
  const [appliedFilters, setAppliedFilters] =
    useState<GroupsFilterState>(emptyFilters());
  const [draftFilters, setDraftFilters] =
    useState<GroupsFilterState>(emptyFilters());

  const hasActiveFilters = Object.values(appliedFilters).some(
    (s) => s.size > 0
  );

  // Filter chips carry exactly the enum values (see the typed constant arrays
  // in RouteGroupsTab), so casting the string Sets to the enum arrays the API
  // expects is safe. Search is local-only UI — the endpoint has no search param.
  const { data: rows = [], isLoading } = useRouteGroups({
    weekday:
      appliedFilters.weekdays.size > 0
        ? ([...appliedFilters.weekdays] as DriveDaysOfWeekEnum[])
        : undefined,
    delivery_type:
      appliedFilters.deliveryTypes.size > 0
        ? ([...appliedFilters.deliveryTypes] as DeliveryTypeEnum[])
        : undefined,
    route_status:
      appliedFilters.routeStatuses.size > 0
        ? ([...appliedFilters.routeStatuses] as RouteStatusEnum[])
        : undefined,
    driver_assignment_status:
      appliedFilters.driverStatuses.size > 0
        ? ([...appliedFilters.driverStatuses] as DriverAssignmentStatusEnum[])
        : undefined,
  });

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
  };

  return {
    rows,
    isLoading,
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
