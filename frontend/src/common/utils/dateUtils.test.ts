import { afterEach, describe, expect, it } from 'vitest';

import {
  formatDriveDate,
  formatShortDate,
  parseDateOnly,
  toNaiveDateString,
} from './dateUtils';

/**
 * The backend sends drive dates as date-only strings ("YYYY-MM-DD"). The
 * browser's own `new Date("YYYY-MM-DD")` reads those as UTC midnight, which
 * west of Greenwich is the previous evening — so the date renders and sorts a
 * day early. These pin the pair of helpers that avoid that.
 */
describe('parseDateOnly', () => {
  it('reads a date-only string as local midnight, not UTC midnight', () => {
    const parsed = parseDateOnly('2026-08-31');

    expect(parsed.getFullYear()).toBe(2026);
    expect(parsed.getMonth()).toBe(7); // August
    expect(parsed.getDate()).toBe(31);
    expect(parsed.getHours()).toBe(0);
  });

  it('keeps the calendar day that new Date() would shift', () => {
    // Only meaningful west of UTC, which is where this app runs; east of it
    // the naive parse happens to agree and there is nothing to assert.
    const parsed = parseDateOnly('2026-08-31');
    const naive = new Date('2026-08-31');

    if (naive.getTimezoneOffset() > 0) {
      expect(naive.getDate()).toBe(30);
      expect(parsed.getDate()).toBe(31);
    } else {
      expect(parsed.getDate()).toBe(31);
    }
  });

  it('ignores a time component, keeping the date part', () => {
    expect(parseDateOnly('2026-01-01T23:30:00Z').getDate()).toBe(1);
    expect(parseDateOnly('2026-01-01T23:30:00Z').getMonth()).toBe(0);
  });

  it('handles month and year boundaries', () => {
    const newYear = parseDateOnly('2027-01-01');
    expect(newYear.getFullYear()).toBe(2027);
    expect(newYear.getMonth()).toBe(0);
    expect(newYear.getDate()).toBe(1);

    const leapDay = parseDateOnly('2028-02-29');
    expect(leapDay.getMonth()).toBe(1);
    expect(leapDay.getDate()).toBe(29);
  });

  it('compares correctly against a local midnight "today"', () => {
    // The driver homepage's actual test: a route dated today must not sort
    // into the past. With `new Date(...)` it did.
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    expect(parseDateOnly(toNaiveDateString(today)) >= today).toBe(true);
    expect(parseDateOnly(toNaiveDateString(today)) < today).toBe(false);
  });

  it('preserves ordering across a month boundary', () => {
    expect(parseDateOnly('2026-08-31') < parseDateOnly('2026-09-01')).toBe(
      true
    );
  });
});

// drive_date is a date-only column. The calendar hands back a local Date, and
// what goes on the wire has to be that same calendar day with no time part —
// the API rejects a datetime whose time isn't midnight, and any UTC round-trip
// can shift the day for anyone west of Greenwich.
describe('toNaiveDateString', () => {
  it('formats a local Date as YYYY-MM-DD', () => {
    expect(toNaiveDateString(new Date(2026, 7, 31))).toBe('2026-08-31');
    expect(toNaiveDateString(new Date(2025, 9, 14))).toBe('2025-10-14');
  });

  it('zero-pads single-digit months and days', () => {
    expect(toNaiveDateString(new Date(2026, 0, 5))).toBe('2026-01-05');
    expect(toNaiveDateString(new Date(2025, 11, 9))).toBe('2025-12-09');
  });

  it('uses the local date even late in the local evening', () => {
    // 23:30 local on Aug 31 is already Sep 1 in UTC; the naive string must
    // still say August, since that is the day the deliveries belong to.
    expect(toNaiveDateString(new Date(2026, 7, 31, 23, 30))).toBe('2026-08-31');
  });

  it('never emits a time part, whatever time of day the Date carries', () => {
    expect(toNaiveDateString(new Date(2025, 9, 14, 23, 59, 59))).toBe(
      '2025-10-14'
    );
    expect(toNaiveDateString(new Date(2025, 9, 14, 0, 0, 0))).toBe(
      '2025-10-14'
    );
  });

  it('keeps the local day at the edges of the year, where UTC would slip', () => {
    expect(toNaiveDateString(new Date(2025, 11, 31, 20, 0))).toBe('2025-12-31');
    expect(toNaiveDateString(new Date(2026, 0, 1, 2, 0))).toBe('2026-01-01');
  });

  it('handles a leap day', () => {
    expect(toNaiveDateString(new Date(2024, 1, 29))).toBe('2024-02-29');
  });

  it('round-trips with parseDateOnly', () => {
    for (const iso of [
      '2024-02-29',
      '2025-12-31',
      '2026-01-01',
      '2026-08-31',
      '2027-12-31',
      '2028-02-29',
    ]) {
      expect(toNaiveDateString(parseDateOnly(iso))).toBe(iso);
    }
  });
});

describe('formatDriveDate', () => {
  const HOST_TIMEZONE = process.env.TZ;

  afterEach(() => {
    process.env.TZ = HOST_TIMEZONE;
  });

  // Spans the offset range: UTC-11 through UTC+14. Only the negative offsets
  // can catch the UTC-midnight bug, but a host in a positive one would
  // otherwise pass a broken implementation without noticing.
  it.each([
    'Pacific/Niue',
    'Pacific/Honolulu',
    'America/Los_Angeles',
    'America/Toronto',
    'UTC',
    'Europe/Berlin',
    'Asia/Tokyo',
    'Pacific/Kiritimati',
  ])('names the date the backend sent, on a clock in %s', (zone) => {
    process.env.TZ = zone;
    expect(formatDriveDate('2026-08-31')).toBe('Aug 31');
  });

  it('holds where the UTC reading crosses a month and a year', () => {
    process.env.TZ = 'America/Toronto';
    expect(formatDriveDate('2026-01-01')).toBe('Jan 1');
  });

  it('takes the date part of a datetime string', () => {
    process.env.TZ = 'America/Toronto';
    expect(formatDriveDate('2026-08-31T00:00:00')).toBe('Aug 31');
  });

  it('returns the input unchanged when it is not a date', () => {
    expect(formatDriveDate('not a date')).toBe('not a date');
  });
});

describe('formatShortDate', () => {
  it('renders MM/DD/YY from a date-only string', () => {
    expect(formatShortDate('2025-10-14')).toBe('10/14/25');
  });

  it('ignores a time part rather than shifting the day', () => {
    expect(formatShortDate('2025-10-14T00:00:00')).toBe('10/14/25');
    expect(formatShortDate('2025-10-14T23:30:00')).toBe('10/14/25');
  });
});
