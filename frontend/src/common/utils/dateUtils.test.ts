import { describe, expect, it } from 'vitest';

import { parseDateOnly, toNaiveDateString } from './dateUtils';

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

describe('toNaiveDateString', () => {
  it('formats a local Date as YYYY-MM-DD', () => {
    expect(toNaiveDateString(new Date(2026, 7, 31))).toBe('2026-08-31');
  });

  it('zero-pads single-digit months and days', () => {
    expect(toNaiveDateString(new Date(2026, 0, 5))).toBe('2026-01-05');
  });

  it('uses the local date even late in the local evening', () => {
    // 23:30 local on Aug 31 is already Sep 1 in UTC; the naive string must
    // still say August, since that is the day the deliveries belong to.
    expect(toNaiveDateString(new Date(2026, 7, 31, 23, 30))).toBe('2026-08-31');
  });

  it('round-trips with parseDateOnly', () => {
    for (const iso of [
      '2026-01-01',
      '2026-08-31',
      '2028-02-29',
      '2027-12-31',
    ]) {
      expect(toNaiveDateString(parseDateOnly(iso))).toBe(iso);
    }
  });
});
