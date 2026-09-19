/** A year/month pair as the reports API returns it (month is 1-12). */
export interface CalendarMonth {
  year: number;
  month: number;
}

/**
 * Build a Date at midday on the 1st of the given month.
 *
 * Midday rather than midnight so `toLocaleDateString` can't roll the label
 * back a day — and therefore a month — under a negative UTC offset.
 */
const monthDate = ({ year, month }: CalendarMonth): Date =>
  new Date(year, month - 1, 1, 12);

/** "Jun" — the axis label under each bar. */
export const formatMonthAbbreviation = (month: CalendarMonth): string =>
  monthDate(month).toLocaleDateString('en-US', { month: 'short' });

/** "June" — the month named beside the highlighted stat. */
export const formatMonthName = (month: CalendarMonth): string =>
  monthDate(month).toLocaleDateString('en-US', { month: 'long' });

/** Step a year/month pair by whole months, rolling the year over as needed. */
export const shiftMonth = (
  { year, month }: CalendarMonth,
  offset: number
): CalendarMonth => {
  const ordinal = year * 12 + (month - 1) + offset;
  return { year: Math.floor(ordinal / 12), month: (ordinal % 12) + 1 };
};

/** Whether two year/month pairs name the same month. */
export const isSameMonth = (a: CalendarMonth, b: CalendarMonth): boolean =>
  a.year === b.year && a.month === b.month;

/**
 * Group counts read as whole numbers; distances carry one decimal until they
 * get large enough that the fraction is noise on a dashboard tile.
 */
export const formatKilometres = (km: number): string =>
  km.toLocaleString('en-US', {
    maximumFractionDigits: km < 100 ? 1 : 0,
  });

export const formatCount = (count: number): string =>
  count.toLocaleString('en-US');
