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
 * Bar fills for the trailing months, cycled oldest-to-newest.
 *
 * The designs show the history in washed-out brand colours with no repeating
 * pattern between frames, so the palette cycles rather than pinning a colour
 * per calendar month — what carries meaning is that the newest month is the
 * one saturated bar (see CURRENT_MONTH_BAR_CLASS), not which hue a given
 * older month landed on.
 */
export const HISTORY_BAR_CLASSES = [
  'bg-brand-orange/20',
  'bg-brand-pink/20',
  'bg-brand-light-blue/20',
  'bg-brand-green/20',
  'bg-blue-300/20',
] as const;

/** The newest month reads as the highlight, matching the blue "In <month>" stat. */
export const CURRENT_MONTH_BAR_CLASS = 'bg-blue-300';
