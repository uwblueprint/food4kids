import type { RouteGroupRead } from '@/api/generated/types.gen';
import { useRouteGroups } from '@/api/route-groups';
import type { UseSearchReturn } from '@/common/hooks';
import { useDebouncedValue, useSearch } from '@/common/hooks';

import type { UseRouteFiltersReturn } from './useRouteFilters';
import { routeFiltersToQuery, useRouteFilters } from './useRouteFilters';

export interface GroupsTabState extends UseRouteFiltersReturn {
  rows: RouteGroupRead[];
  isLoading: boolean;
  search: UseSearchReturn;
  /** Debounced search term the rows were filtered by, for highlighting. */
  searchTerm: string;
}

export function useGroupsTabState(): GroupsTabState {
  const search = useSearch();
  const filters = useRouteFilters();

  // Debounced so the server query fires once typing pauses. Filters by the
  // group name (GET /route-groups?search); the chips narrow server-side too.
  const debouncedSearch = useDebouncedValue(search.value);

  const { data: rows = [], isLoading } = useRouteGroups({
    search: debouncedSearch.trim() || undefined,
    ...routeFiltersToQuery(filters.appliedFilters),
  });

  return {
    ...filters,
    rows,
    isLoading,
    search,
    searchTerm: debouncedSearch.trim(),
  };
}
