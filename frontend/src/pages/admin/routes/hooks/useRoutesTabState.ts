import { useMemo, useState } from 'react';

import type { RouteWithDateRead } from '@/api/generated/types.gen';
import { useRoutes } from '@/api/routes';
import type { UsePaginationReturn, UseSearchReturn } from '@/common/hooks';
import {
  clampPage,
  TABLE_PAGE_SIZE,
  useDebouncedValue,
  usePagination,
  useSearch,
} from '@/common/hooks';

import type { UseRouteFiltersReturn } from './useRouteFilters';
import { routeFiltersToQuery, useRouteFilters } from './useRouteFilters';

export interface RoutesTabState
  extends UseRouteFiltersReturn, UsePaginationReturn {
  rows: RouteWithDateRead[];
  totalPages: number;
  search: UseSearchReturn;
  /** Debounced search term the rows were filtered by, for highlighting. */
  searchTerm: string;
  /** Routes with no driver, across the filters but ignoring the search box. */
  unassignedCount: number;
  bannerDismissed: boolean;
  dismissBanner: () => void;
}

export function useRoutesTabState(): RoutesTabState {
  const search = useSearch();
  const filters = useRouteFilters();
  const [bannerDismissed, setBannerDismissed] = useState(false);

  // Debounced so the server query fires once typing pauses. Filters by driver
  // name, route name, or group name (GET /routes?search); the chips narrow
  // server-side too.
  const searchTerm = useDebouncedValue(search.value).trim();

  const filterQuery = routeFiltersToQuery(filters.appliedFilters);
  const query = { search: searchTerm || undefined, ...filterQuery };
  const { page: requestedPage, setPage } = usePagination(JSON.stringify(query));
  const { data } = useRoutes({
    ...query,
    page: requestedPage,
    page_size: TABLE_PAGE_SIZE,
  });
  const rows = useMemo(() => data?.items ?? [], [data]);
  const totalPages = data?.total_pages ?? 0;

  // Counted server-side rather than from `rows`: the banner is about the whole
  // filtered result set and `rows` is one page of it. page_size 1 because only
  // the total is wanted — the item itself is thrown away. Both the
  // driver-assignment chip and the search box are deliberately dropped: the
  // banner answers "how many routes still need a driver", and a search that
  // matches a driver's name can never match an unassigned route, so carrying
  // it through would zero the banner out for reasons unrelated to the answer.
  const { data: unassigned } = useRoutes({
    ...filterQuery,
    driver_assignment_status: ['Unassigned'],
    page_size: 1,
  });

  return {
    ...filters,
    rows,
    page: clampPage(requestedPage, totalPages, setPage),
    setPage,
    totalPages,
    search,
    searchTerm,
    unassignedCount: unassigned?.total ?? 0,
    bannerDismissed,
    dismissBanner: () => setBannerDismissed(true),
  };
}
