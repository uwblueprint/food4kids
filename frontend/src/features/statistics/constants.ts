/** How many months of history the widget's bar charts show. */
export const SERIES_MONTHS = 6;

/** How many drivers the "Top Drivers" ranking lists. */
export const TOP_DRIVERS_LIMIT = 5;

/** The three views the widget's title dropdown switches between. */
export const STATISTIC_VIEWS = [
  { id: 'distance', label: 'Distance Driven' },
  { id: 'deliveries', label: 'Deliveries Made' },
  { id: 'drivers', label: 'Top Drivers' },
] as const;

export type StatisticView = (typeof STATISTIC_VIEWS)[number]['id'];

/**
 * Bar fills for the six months, cycled oldest-to-newest.
 *
 * The palette cycles rather than pinning a colour per calendar month — what
 * carries meaning is that the newest month is the one bar at full strength
 * and the history sits at 20%, not which hue a given older month landed on.
 */
export const BAR_COLOR_CLASSES = [
  'bg-brand-orange',
  'bg-brand-pink',
  'bg-brand-light-blue',
  'bg-brand-green',
  'bg-blue-300',
] as const;

/** Everything but the newest month is washed out to 20%. */
export const HISTORY_BAR_OPACITY = 'opacity-20';
