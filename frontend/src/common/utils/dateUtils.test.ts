import { describe, expect, it } from 'vitest';

import { formatShortDate, parseDateOnly, toNaiveDateString } from './dateUtils';

// drive_date is a date-only column. The calendar hands back a local Date, and
// what goes on the wire has to be that same calendar day with no time part —
// the API rejects a datetime whose time isn't midnight, and any UTC round-trip
// can shift the day for anyone west of Greenwich.
describe('toNaiveDateString', () => {
  it('formats a local Date as YYYY-MM-DD', () => {
    expect(toNaiveDateString(new Date(2025, 9, 14))).toBe('2025-10-14');
  });

  it('zero-pads single-digit months and days', () => {
    expect(toNaiveDateString(new Date(2025, 0, 5))).toBe('2025-01-05');
    expect(toNaiveDateString(new Date(2025, 11, 9))).toBe('2025-12-09');
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

  it('round-trips through parseDateOnly', () => {
    for (const iso of ['2024-02-29', '2025-01-01', '2025-12-31']) {
      expect(toNaiveDateString(parseDateOnly(iso))).toBe(iso);
    }
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
