import { useQuery } from '@tanstack/react-query';

import {
  getMonthlyRankingOptions,
  getMonthlySeriesOptions,
} from './generated/@tanstack/react-query.gen';

/**
 * GET /reports/monthly-series — km and deliveries per month for a trailing
 * window, oldest first, backing the homepage statistics bar charts.
 *
 * One request covers both metrics, so the "Distance Driven" and "Deliveries
 * Made" views of the widget share a single cache entry and neither refetches
 * when the user toggles between them.
 *
 * `end_year`/`end_month` are omitted so the backend anchors the window on the
 * current month in F4K's timezone — the browser's clock may disagree.
 */
export function useMonthlySeries(months: number) {
  return useQuery(getMonthlySeriesOptions({ query: { months } }));
}

/**
 * GET /reports/monthly/{year}/{month}/ranking — drivers ranked by km driven
 * in one month, descending, backing the widget's "Top Drivers" view.
 *
 * `enabled` lets the caller hold the request until a month is known (the
 * ranking is anchored on the series' newest month, which arrives async).
 */
export function useMonthlyDriverRanking(
  month: { year: number; month: number } | undefined
) {
  return useQuery({
    ...getMonthlyRankingOptions({
      path: { year: month?.year ?? 0, month: month?.month ?? 1 },
    }),
    enabled: month !== undefined,
  });
}
