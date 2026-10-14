import type { EmailReminder } from '@/api/generated/types.gen';

/** "Up to three notifications can be set", per the design. */
export const MAX_REMINDERS = 3;

export const ADD_REMINDER_LIMIT_MESSAGE =
  "You've reached the limit of three automated reminders";

/**
 * Lead days offered in the "How many days before?" dropdown. Starts at 0
 * ("Day of"), which the design shows and the model permits; the ceiling is a
 * UI choice that keeps the list scannable.
 */
const MIN_DAYS_BEFORE = 0;
const MAX_DAYS_BEFORE = 7;

const DAYS_BEFORE_OPTIONS = Array.from(
  { length: MAX_DAYS_BEFORE - MIN_DAYS_BEFORE + 1 },
  (_, i) => i + MIN_DAYS_BEFORE
);

/**
 * A reminder the admin has added but not yet given a lead time. `days_before`
 * is a required non-negative int on the wire, so this only lives in the draft
 * and the save is blocked while any reminder carries it.
 */
export const UNSET_DAYS_BEFORE = -1;

export function isReminderComplete(reminder: EmailReminder): boolean {
  return reminder.days_before !== UNSET_DAYS_BEFORE;
}

/** Offers `value` alongside the list when a saved row sits outside the range. */
export function daysBeforeOptionsFor(value: number): number[] {
  // The sentinel is a placeholder, not a lead time, so it is never offered.
  if (value < 0 || DAYS_BEFORE_OPTIONS.includes(value)) {
    return DAYS_BEFORE_OPTIONS;
  }
  return [...DAYS_BEFORE_OPTIONS, value].sort((a, b) => a - b);
}

export function formatDaysBefore(days: number): string {
  if (days === 0) return 'Day of';
  return days === 1 ? '1 day before' : `${days} days before`;
}

/** A new row has no lead time chosen, so the admin has to pick one. */
export function createReminder(): EmailReminder {
  return { days_before: UNSET_DAYS_BEFORE, time: '09:00:00' };
}
