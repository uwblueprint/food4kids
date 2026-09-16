import type {
  RouteGroupRead,
  RouteWithDateRead,
} from '@/api/generated/types.gen';
import type { Column } from '@/common/components';
import { formatShortDate, parseDateOnly } from '@/common/utils';

import { DriveDateCell } from './DriveDateCell';

/**
 * Date column for the Routes tab — read-only on purpose.
 *
 * A drive date lives on RouteGroup; Route has no date of its own. Editing it
 * from a route row therefore moved every sibling route in the group, with
 * nothing in the UI saying so. The calendar is offered on the Groups tab only,
 * where the thing being edited is the thing being displayed.
 */
export const routeDriveDateColumn: Column<RouteWithDateRead> = {
  key: 'drive_date',
  header: 'Delivery Date',
  sortable: true,
  sortValue: (row) => parseDateOnly(row.drive_date),
  render: (row) => formatShortDate(row.drive_date),
};

/**
 * Date column for the Groups tab — editable via the hover calendar.
 *
 * `onUpdated` receives the group id, so the tab can highlight the row the
 * re-sort just moved.
 */
export const routeGroupDriveDateColumn = (
  onUpdated?: (routeGroupId: string) => void
): Column<RouteGroupRead> => ({
  key: 'drive_date',
  header: 'Date',
  sortable: true,
  sortValue: (row) => parseDateOnly(row.drive_date),
  render: (row) => (
    <DriveDateCell
      routeGroupId={row.route_group_id}
      driveDate={row.drive_date}
      onUpdated={onUpdated ? () => onUpdated(row.route_group_id) : undefined}
    />
  ),
});
