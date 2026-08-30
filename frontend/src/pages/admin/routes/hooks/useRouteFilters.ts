import { useState } from 'react';

import type {
  DriveDaysOfWeekEnum,
  DriverAssignmentStatusEnum,
  RouteStatusEnum,
} from '@/api/generated/types.gen';
import { useSystemSettings } from '@/api/system-settings';

/**
 * The filter set shared by the Groups and Routes tabs: weekday, delivery type,
 * route status, and driver-assignment status.
 */
export interface RouteFilterState {
  weekdays: Set<DriveDaysOfWeekEnum>;
  deliveryTypes: Set<string>;
  routeStatuses: Set<RouteStatusEnum>;
  driverStatuses: Set<DriverAssignmentStatusEnum>;
}

type SetElement<S> = S extends Set<infer V> ? V : never;

const emptyFilters = (): RouteFilterState => ({
  weekdays: new Set(),
  deliveryTypes: new Set(),
  routeStatuses: new Set(),
  driverStatuses: new Set(),
});

const copyFilters = (f: RouteFilterState): RouteFilterState => ({
  weekdays: new Set(f.weekdays),
  deliveryTypes: new Set(f.deliveryTypes),
  routeStatuses: new Set(f.routeStatuses),
  driverStatuses: new Set(f.driverStatuses),
});

/** Convert applied filters into GET query params (shared by both tabs). */
export const routeFiltersToQuery = (f: RouteFilterState) => ({
  weekday: f.weekdays.size > 0 ? [...f.weekdays] : undefined,
  delivery_type: f.deliveryTypes.size > 0 ? [...f.deliveryTypes] : undefined,
  route_status: f.routeStatuses.size > 0 ? [...f.routeStatuses] : undefined,
  driver_assignment_status:
    f.driverStatuses.size > 0 ? [...f.driverStatuses] : undefined,
});

export interface UseRouteFiltersReturn {
  /** Configured delivery types, for the Delivery Type chips. */
  deliveryTypes: string[];
  filterOpen: boolean;
  setFilterOpen: (v: boolean) => void;
  /** The filters currently applied to the query. */
  appliedFilters: RouteFilterState;
  /** The in-dialog draft, applied on handleApply. */
  draftFilters: RouteFilterState;
  hasActiveFilters: boolean;
  openFilters: () => void;
  toggleDraft: <K extends keyof RouteFilterState>(
    key: K,
    value: SetElement<RouteFilterState[K]>
  ) => void;
  /** True when the draft has at least one chip selected (Clear All enabled). */
  draftHasSelections: boolean;
  /** Unselect every chip in the dialog; takes effect on Apply. */
  clearDraft: () => void;
  handleApply: () => void;
}

/**
 * Filter-dialog state for the Groups and Routes tabs. Owns the draft/applied
 * filters and the open/toggle/apply/clear handlers; the consumer feeds
 * `appliedFilters` (via routeFiltersToQuery) into its own list query.
 */
export function useRouteFilters(): UseRouteFiltersReturn {
  const [filterOpen, setFilterOpen] = useState(false);
  const [appliedFilters, setAppliedFilters] =
    useState<RouteFilterState>(emptyFilters());
  const [draftFilters, setDraftFilters] =
    useState<RouteFilterState>(emptyFilters());
  const { data: systemSettings } = useSystemSettings();
  // Empty until settings load; the filter dialog hides the group either way.
  const deliveryTypes = systemSettings?.delivery_types ?? [];

  const hasActiveFilters = Object.values(appliedFilters).some(
    (s) => s.size > 0
  );
  const draftHasSelections = Object.values(draftFilters).some(
    (s) => s.size > 0
  );

  const openFilters = () => {
    setDraftFilters(copyFilters(appliedFilters));
    setFilterOpen(true);
  };

  const toggleDraft = <K extends keyof RouteFilterState>(
    key: K,
    value: SetElement<RouteFilterState[K]>
  ) => {
    setDraftFilters((prev) => {
      const next = new Set(prev[key]);
      if (next.has(value)) next.delete(value);
      else next.add(value);
      return { ...prev, [key]: next };
    });
  };

  const clearDraft = () => setDraftFilters(emptyFilters());

  const handleApply = () => {
    setAppliedFilters(copyFilters(draftFilters));
    setFilterOpen(false);
  };

  return {
    deliveryTypes,
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
