export const formatDisplayDate = (date: Date): string =>
  date.toLocaleDateString('en-US', { month: 'long', day: 'numeric' });

/**
 * Format an ISO date(-time) string as MM/DD/YY (e.g. "10/14/25").
 * Works on the string's date part directly so a naive backend datetime
 * ("2025-10-14T00:00:00") never shifts a day from timezone conversion.
 */
export const formatShortDate = (isoDate: string): string => {
  const [datePart] = isoDate.split('T');
  const [year, month, day] = datePart.split('-');
  return `${month}/${day}/${year.slice(-2)}`;
};

/**
 * Format a local Date as "YYYY-MM-DD" without timezone conversion, for
 * building the API's naive datetime strings.
 */
export const toNaiveDateString = (date: Date): string => {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
};

/**
 * Parse the date part of an ISO date(-time) string as a local Date at
 * midnight, avoiding the UTC interpretation of `new Date("YYYY-MM-DD")`.
 */
export const parseDateOnly = (isoDate: string): Date => {
  const [datePart] = isoDate.split('T');
  const [year, month, day] = datePart.split('-').map(Number);
  return new Date(year, month - 1, day);
};
