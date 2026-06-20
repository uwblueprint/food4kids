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
  weekdays: Set<DriveDaysOfWeekEnum>;
  deliveryTypes: Set<DeliveryTypeEnum>;
  routeStatuses: Set<RouteStatusEnum>;
  driverStatuses: Set<DriverAssignmentStatusEnum>;
}

type SetElement<S> = S extends Set<infer V> ? V : never;

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
  toggleDraft: <K extends keyof GroupsFilterState>(
    key: K,
    value: SetElement<GroupsFilterState[K]>
  ) => void;
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

  // Search is local-only UI — the endpoint has no search param yet, so only the
  // filter chips hit the server.
  const { data: rows = [], isLoading } = useRouteGroups({
    weekday:
      appliedFilters.weekdays.size > 0
        ? [...appliedFilters.weekdays]
        : undefined,
    delivery_type:
      appliedFilters.deliveryTypes.size > 0
        ? [...appliedFilters.deliveryTypes]
        : undefined,
    route_status:
      appliedFilters.routeStatuses.size > 0
        ? [...appliedFilters.routeStatuses]
        : undefined,
    driver_assignment_status:
      appliedFilters.driverStatuses.size > 0
        ? [...appliedFilters.driverStatuses]
        : undefined,
  });

  const openFilters = () => {
    setDraftFilters(copyFilters(appliedFilters));
    setFilterOpen(true);
  };

  const toggleDraft = <K extends keyof GroupsFilterState>(
    key: K,
    value: SetElement<GroupsFilterState[K]>
  ) => {
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
