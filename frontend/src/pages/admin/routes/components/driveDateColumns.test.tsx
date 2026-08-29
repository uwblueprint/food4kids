import type { ComponentProps, ReactElement } from 'react';
import { isValidElement } from 'react';
import { describe, expect, it } from 'vitest';

import type {
  RouteGroupRead,
  RouteWithDateRead,
} from '@/api/generated/types.gen';

import { DriveDateCell } from './DriveDateCell';
import {
  routeDriveDateColumn,
  routeGroupDriveDateColumn,
} from './driveDateColumns';

type CellProps = ComponentProps<typeof DriveDateCell>;

const group = (overrides: Partial<RouteGroupRead> = {}): RouteGroupRead => ({
  route_group_id: 'group-1',
  name: 'Tuesday AM',
  notes: '',
  drive_date: '2025-10-14',
  num_routes: 3,
  num_locations: 20,
  num_boxes: 24,
  num_drivers_assigned: 3,
  delivery_type: 'Regular',
  status: 'Upcoming',
  frozen: false,
  routes: [],
  ...overrides,
});

const route = (
  overrides: Partial<RouteWithDateRead> = {}
): RouteWithDateRead => ({
  route_id: 'route-1',
  route_group_id: 'group-1',
  group_name: 'Tuesday AM',
  name: 'Route 1',
  notes: '',
  drive_date: '2025-10-14',
  num_stops: 8,
  box_total: 10,
  length: 23.4,
  driver_name: 'Sam Driver',
  delivery_type: 'Regular',
  start_time: '08:00:00',
  status: 'Upcoming',
  ...overrides,
});

/** Renders the Groups-tab cell and narrows the node to the cell's props. */
const groupCell = (
  row: RouteGroupRead,
  onUpdated?: (routeGroupId: string) => void
): ReactElement<CellProps> =>
  routeGroupDriveDateColumn(onUpdated).render!(row) as ReactElement<CellProps>;

describe('routeDriveDateColumn (Routes tab)', () => {
  // The date lives on RouteGroup — a Route has none of its own — so editing it
  // from a route row moved every sibling route in the group, silently. The
  // cell is plain text now: no element, so nothing to hover, click, or PATCH.
  it('renders the date as plain text, not an editable cell', () => {
    const node = routeDriveDateColumn.render!(route());
    expect(node).toBe('10/14/25');
    expect(isValidElement(node)).toBe(false);
  });

  it('never renders the editable cell, whatever the date', () => {
    for (const drive_date of ['2024-01-02', '2025-12-31', '2030-06-05']) {
      const node = routeDriveDateColumn.render!(route({ drive_date }));
      expect(isValidElement(node)).toBe(false);
    }
  });

  it('keeps the column sortable by date', () => {
    expect(routeDriveDateColumn.sortable).toBe(true);
    expect(routeDriveDateColumn.sortValue!(route())).toEqual(
      new Date('2025-10-14')
    );
  });
});

describe('routeGroupDriveDateColumn (Groups tab)', () => {
  it('renders the editable cell, where the date actually belongs', () => {
    const node = groupCell(group());
    expect(isValidElement(node)).toBe(true);
    expect(node.type).toBe(DriveDateCell);
  });

  it('passes the group id and date through to the cell', () => {
    const node = groupCell(
      group({ route_group_id: 'group-9', drive_date: '2026-02-03' })
    );
    expect(node.props.routeGroupId).toBe('group-9');
    expect(node.props.driveDate).toBe('2026-02-03');
  });

  it('marks a frozen group so the cell drops the calendar', () => {
    expect(groupCell(group({ frozen: true })).props.frozen).toBe(true);
  });

  it('leaves an unfrozen group editable', () => {
    expect(groupCell(group({ frozen: false })).props.frozen).toBe(false);
  });

  it('reports the edited group back so the tab can highlight the row', () => {
    const seen: string[] = [];
    const node = groupCell(group({ route_group_id: 'group-7' }), (id) => {
      seen.push(id);
    });
    node.props.onUpdated!();
    expect(seen).toEqual(['group-7']);
  });

  it('omits onUpdated when the caller supplies no handler', () => {
    expect(groupCell(group()).props.onUpdated).toBeUndefined();
  });
});
