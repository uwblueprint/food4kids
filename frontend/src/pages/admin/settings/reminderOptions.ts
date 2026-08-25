import type { EmailReminder } from '@/api/generated/types.gen';

/** "Up to three notifications can be set", per the design. */
export const MAX_REMINDERS = 3;

export const ADD_REMINDER_LIMIT_MESSAGE =
  "You've reached the limit of three automated reminders";

/**
 * Lead days offered in the "How many days before?" dropdown.
 *
 * Starts at 1, not 0: a reminder is meant to arrive *ahead* of the route, so
 * "day of" is not a lead time an admin should be able to pick. The model still
 * permits `days_before >= 0`, and the Figma shows "Day of" on Notification 1 --
 * this is a deliberate product decision to require a real day.
 *
 * The ceiling is a UI choice: a week covers the cadence the design shows with
 * room either side, and keeps the list scannable.
 */
const MIN_DAYS_BEFORE = 1;
const MAX_DAYS_BEFORE = 7;

export const DAYS_BEFORE_OPTIONS = Array.from(
  { length: MAX_DAYS_BEFORE - MIN_DAYS_BEFORE + 1 },
  (_, i) => i + MIN_DAYS_BEFORE
);

/**
 * The options to offer for a reminder whose stored lead is `value`.
 *
 * Rows saved before this rule existed -- the seed still creates a day-of
 * reminder -- can sit outside the list, and Radix Select renders an unmatched
 * value as blank. Including the stored value keeps the row truthful and
 * editable; it just is not offered to anything that does not already use it.
 */
export function daysBeforeOptionsFor(value: number): number[] {
  if (DAYS_BEFORE_OPTIONS.includes(value)) return DAYS_BEFORE_OPTIONS;
  return [...DAYS_BEFORE_OPTIONS, value].sort((a, b) => a - b);
}

export function formatDaysBefore(days: number): string {
  if (days === 0) return 'Day of';
  return days === 1 ? '1 day before' : `${days} days before`;
}

const TIME_STEP_MINUTES = 30;

function toTimeValue(hour: number, minute: number): string {
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${pad(hour)}:${pad(minute)}:00`;
}

export const TIME_OPTIONS = Array.from(
  { length: (24 * 60) / TIME_STEP_MINUTES },
  (_, slot) => {
    const totalMinutes = slot * TIME_STEP_MINUTES;
    return toTimeValue(Math.floor(totalMinutes / 60), totalMinutes % 60);
  }
);

export function formatTimeLabel(value: string): string {
  const [hourRaw = 0, minuteRaw = 0] = value.split(':').map(Number);
  const period = hourRaw >= 12 ? 'PM' : 'AM';
  const hour = hourRaw % 12 === 0 ? 12 : hourRaw % 12;
  return `${hour}:${String(minuteRaw).padStart(2, '0')} ${period}`;
}

/**
 * The options to offer for a reminder whose stored time is `value`.
 *
 * A reminder saved before this screen existed -- or seeded -- can sit off the
 * 30-minute grid, and Radix Select renders a value with no matching item as
 * blank. Rounding the *display* onto the grid would be worse than blank: the
 * row would claim a time the reminder does not actually fire at, and editing
 * any other part of that row would carry the real time through to the PATCH
 * unchanged. Offering the stored value as its own option keeps what is shown
 * and what is saved identical.
 */
export function timeOptionsFor(value: string): string[] {
  if (TIME_OPTIONS.includes(value)) return TIME_OPTIONS;
  return [...TIME_OPTIONS, value].sort();
}

/** A new row copies the model's own default rather than inventing a time. */
export function createReminder(): EmailReminder {
  return { days_before: 1, time: '09:00:00' };
}
