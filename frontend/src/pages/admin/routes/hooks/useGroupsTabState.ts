import type { RouteGroupRead } from '@/api/generated/types.gen';
import { useRouteGroups } from '@/api/route-groups';
import type {
  UsePaginationReturn,
  UseSearchReturn,
  UseTableSortReturn,
} from '@/common/hooks';
import {
  clampPage,
  TABLE_PAGE_SIZE,
  useDebouncedValue,
  usePagination,
  useSearch,
  useTableSort,
} from '@/common/hooks';

import type { UseRouteFiltersReturn } from './useRouteFilters';
import { routeFiltersToQuery, useRouteFilters } from './useRouteFilters';

const SORT_KEYS = {
  drive_date: 'drive_date',
  delivery_type: 'delivery_type',
  status: 'status',
} as const;

export interface GroupsTabState
  extends UseRouteFiltersReturn, UsePaginationReturn, UseTableSortReturn {
  rows: RouteGroupRead[];
  isLoading: boolean;
  totalPages: number;
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

  // Server-side so the sort spans all pages.
  const { sort, toggleSort } = useTableSort();
  const sortKey = SORT_KEYS[sort?.key as keyof typeof SORT_KEYS];

  const query = {
    search: debouncedSearch.trim() || undefined,
    ...routeFiltersToQuery(filters.appliedFilters),
    ...(sortKey && { sort_by: sortKey, order: sort?.dir }),
  };
  const { page, setPage } = usePagination(JSON.stringify(query));

  const { data, isLoading } = useRouteGroups({
    ...query,
    page,
    page_size: TABLE_PAGE_SIZE,
  });

  const totalPages = data?.total_pages ?? 0;

  return {
    ...filters,
    rows: data?.items ?? [],
    sort,
    toggleSort,
    isLoading,
    page: clampPage(page, totalPages, setPage),
    setPage,
    totalPages,
    search,
    searchTerm: debouncedSearch.trim(),
  };
}
