// @vitest-environment happy-dom
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
 * `data-day` as the component writes it. Going through the same
 * `toLocaleDateString()` call keeps the test's idea of the format from
 * disagreeing with the component's under any runner locale.
 */
function dataDay(year: number, month: number, day: number): string {
  return new Date(year, month, day).toLocaleDateString();
}

/** Every day button in the grid, in DOM order, with the date it stands for. */
function dayCells(container: HTMLElement) {
  return [...container.querySelectorAll<HTMLElement>('button[data-day]')].map(
    (el) => {
      const day = el.dataset.day;
      if (!day) throw new Error('day button without a data-day');
      return { el, day, label: el.textContent?.trim() ?? '' };
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
    // Fixture check: the grid's first cell, Dec 29 2025, is a Monday.
    expect(new Date(2025, 11, 29).getDay()).toBe(1);

    const cells = dayCells(container);
    expect(cells.length % 7).toBe(0);
    // Seven-wide rows of consecutive days from a Monday: every row therefore
    // runs Monday through Sunday.
    expect(cells.map((cell) => cell.day)).toEqual(
      cells.map((_, i) => dataDay(2025, 11, 29 + i))
    );
    for (const row of weekRows(container)) expect(row).toHaveLength(7);
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
    expect(weekRows(container)[0][0].day).toBe(dataDay(2025, 11, 28));
  });
});

describe('Calendar selection', () => {
  /**
   * The Monday-first change reorders columns only. Guard against it shifting
   * which date a cell stands for by clicking cells at both ends of a row.
   */
  it.each([
    15, // mid-month, a Thursday
    5, // first column of its row, a Monday
    4, // last column of its row, a Sunday
    31, // last day of the month, a Saturday
  ])('clicking Jan %i selects that date', (day) => {
    const onSelect = vi.fn();
    const { container } = render(
      <Calendar mode="single" defaultMonth={JANUARY_2026} onSelect={onSelect} />
    );

    const cell = dayCells(container).find(
      (c) => c.day === dataDay(2026, 0, day)
    );
    expect(cell).toBeDefined();
    expect(cell!.label).toBe(String(day));

    fireEvent.click(cell!.el);

    expect(onSelect).toHaveBeenCalledTimes(1);
    const selected = onSelect.mock.calls[0][0] as Date;
    expect([
      selected.getFullYear(),
      selected.getMonth(),
      selected.getDate(),
    ]).toEqual([2026, 0, day]);
  });

  it('maps every in-month cell to its own date', () => {
    const { container } = render(
      <Calendar mode="single" defaultMonth={JANUARY_2026} />
    );
    const cells = dayCells(container);
    for (let day = 1; day <= 31; day++) {
      const matches = cells.filter((c) => c.day === dataDay(2026, 0, day));
      expect(matches).toHaveLength(1);
      expect(matches[0].label).toBe(String(day));
    }
  });
});
