// @vitest-environment jsdom
import { cleanup, fireEvent, render } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { Calendar } from '@/common/components/Calendar';

afterEach(cleanup);

/**
 * January 2026 is a good fixture: the 1st falls on a Thursday, so a Monday-first
 * grid opens with Dec 29–31 and a Sunday-first grid opens with Dec 28. The two
 * layouts are therefore distinguishable on the very first cell.
 */
const JANUARY_2026 = new Date(2026, 0, 1);

function weekdayHeader(container: HTMLElement): string[] {
  return [...container.querySelectorAll('thead th')].map(
    (th) => th.textContent ?? ''
  );
}

/**
 * `data-day` is `toLocaleDateString()`, so its shape follows the runner's
 * locale: `2026-01-15` under en-CA, `1/15/2026` under en-US. Parse both as a
 * LOCAL date — `new Date('2026-01-15')` would be read as UTC midnight and land
 * on the previous day west of Greenwich.
 */
function parseDataDay(raw: string): Date {
  const parts = raw.match(/\d+/g);
  if (!parts || parts.length !== 3) {
    throw new Error(`unrecognised data-day: ${raw}`);
  }
  const [a, b, c] = parts.map(Number);
  return parts[0].length === 4
    ? new Date(a, b - 1, c) // year-first
    : new Date(c, a - 1, b); // month-first
}

/** Every day button in the grid, in DOM order, with the date it stands for. */
function dayCells(container: HTMLElement) {
  return [...container.querySelectorAll<HTMLElement>('button[data-day]')].map(
    (el) => {
      const raw = el.dataset.day;
      if (!raw) throw new Error('day button without a data-day');
      return {
        el,
        date: parseDataDay(raw),
        label: el.textContent?.trim() ?? '',
      };
    }
  );
}

function weekRows(container: HTMLElement) {
  const rows = new Map<Element, ReturnType<typeof dayCells>>();
  for (const cell of dayCells(container)) {
    const row = cell.el.closest('tr');
    if (!row) throw new Error('day button outside a week row');
    rows.set(row, [...(rows.get(row) ?? []), cell]);
  }
  return [...rows.values()];
}

describe('Calendar weekday order', () => {
  it('renders the header as M T W T F S S', () => {
    const { container } = render(
      <Calendar mode="single" defaultMonth={JANUARY_2026} />
    );
    expect(weekdayHeader(container)).toEqual([
      'M',
      'T',
      'W',
      'T',
      'F',
      'S',
      'S',
    ]);
  });

  it('starts every week row on a Monday and ends it on a Sunday', () => {
    const { container } = render(
      <Calendar mode="single" defaultMonth={JANUARY_2026} />
    );
    const rows = weekRows(container);
    expect(rows.length).toBeGreaterThan(0);

    for (const row of rows) {
      expect(row).toHaveLength(7);
      // 1 = Monday … 0 = Sunday
      expect(row.map((cell) => cell.date.getDay())).toEqual([
        1, 2, 3, 4, 5, 6, 0,
      ]);
    }
  });

  it('opens January 2026 on Dec 29 (Monday), not Dec 28 (Sunday)', () => {
    const { container } = render(
      <Calendar mode="single" defaultMonth={JANUARY_2026} />
    );
    const [firstRow] = weekRows(container);
    expect(firstRow.map((cell) => cell.label)).toEqual([
      '29',
      '30',
      '31',
      '1',
      '2',
      '3',
      '4',
    ]);
  });

  it('still honours an explicit weekStartsOn override', () => {
    const { container } = render(
      <Calendar mode="single" defaultMonth={JANUARY_2026} weekStartsOn={0} />
    );
    expect(weekdayHeader(container)).toEqual([
      'S',
      'M',
      'T',
      'W',
      'T',
      'F',
      'S',
    ]);
    expect(weekRows(container)[0][0].label).toBe('28');
  });
});

describe('Calendar selection', () => {
  /**
   * The Monday-first change reorders columns only. Guard against it shifting
   * which date a cell stands for by clicking cells at both ends of a row.
   */
  it.each([
    ['15', 2026, 0, 15], // mid-month, a Thursday
    ['5', 2026, 0, 5], // first column of its row, a Monday
    ['4', 2026, 0, 4], // last column of its row, a Sunday
    ['31', 2026, 0, 31], // last day of the month, a Saturday
  ])('clicking %s selects the matching date', (label, year, month, day) => {
    const onSelect = vi.fn();
    const { container } = render(
      <Calendar mode="single" defaultMonth={JANUARY_2026} onSelect={onSelect} />
    );

    // Restrict to in-month cells so outside-day duplicates (Dec 29–31) can't
    // be picked up by the label match.
    const cell = dayCells(container).find(
      (c) => c.label === label && c.date.getMonth() === month
    );
    expect(cell).toBeDefined();

    fireEvent.click(cell!.el);

    expect(onSelect).toHaveBeenCalledTimes(1);
    const selected = onSelect.mock.calls[0][0] as Date;
    expect([
      selected.getFullYear(),
      selected.getMonth(),
      selected.getDate(),
    ]).toEqual([year, month, day]);
  });

  it('maps every in-month cell to its own date', () => {
    const { container } = render(
      <Calendar mode="single" defaultMonth={JANUARY_2026} />
    );
    const inMonth = dayCells(container).filter(
      (c) => c.date.getMonth() === 0 && c.date.getFullYear() === 2026
    );
    expect(inMonth).toHaveLength(31);
    expect(inMonth.map((c) => c.label)).toEqual(
      Array.from({ length: 31 }, (_, i) => String(i + 1))
    );
  });
});
