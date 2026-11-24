export const formatDisplayDate = (date: Date): string =>
  date.toLocaleDateString('en-US', { month: 'long', day: 'numeric' });

/**
 * Format a 24-hour time string (e.g. "14:30:00" or "08:00") into a 12-hour
 * AM/PM format (e.g. "2:30 PM" or "8:00 AM"). Returns null if invalid or empty.
 */
export const formatStartTime = (
  value: string | null | undefined
): string | null => {
  if (!value) return null;
  const [h, m] = value.split(':');
  const hour = Number(h);
  const minute = Number(m);
  if (Number.isNaN(hour) || Number.isNaN(minute)) return null;
  const period = hour < 12 ? 'AM' : 'PM';
  const hour12 = hour % 12 === 0 ? 12 : hour % 12;
  return `${hour12}:${String(minute).padStart(2, '0')} ${period}`;
};

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

/**
 * True when `date` falls on a calendar day before today. Compares the naive
 * "YYYY-MM-DD" strings so the answer matches the day the admin sees in the
 * calendar, whatever time of day it is.
 */
export const isPastDate = (date: Date): boolean =>
  toNaiveDateString(date) < toNaiveDateString(new Date());

/**
 * Format a drive date as "Aug 31" — the form the driver and admin views show
 * beside a route. Goes through `parseDateOnly`, so the day it names is the day
 * the backend sent rather than the one the host clock lands on.
 */
export const formatDriveDate = (isoDate: string): string => {
  const date = parseDateOnly(isoDate);
  if (Number.isNaN(date.getTime())) return isoDate;
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
};
