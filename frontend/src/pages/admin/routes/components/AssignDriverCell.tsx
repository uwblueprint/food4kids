import { useState } from 'react';

import type { RouteWithDateRead } from '@/api/generated/types.gen';
import { Button } from '@/common/components';
import { parseDateOnly } from '@/common/utils';

import { ReassignDriverModal } from './ReassignDriverModal';

/** "Oct 18" — short date for the dialog's context line. */
const formatContextDate = (isoDate: string): string =>
  parseDateOnly(isoDate).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  });

interface AssignDriverCellProps {
  row: RouteWithDateRead;
  /** Called once a driver is assigned, e.g. to highlight the row. */
  onUpdated?: () => void;
}

/**
 * The Driver cell for a route nobody is driving yet: a pill that opens the
 * same driver picker the kebab's "Reassign Driver" opens. Per the design the
 * gap is an action rather than a warning — the count of unassigned routes is
 * already called out by the banner above the table.
 */
export function AssignDriverCell({ row, onUpdated }: AssignDriverCellProps) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <Button shape="compact" onClick={() => setOpen(true)}>
        Assign
      </Button>
      <ReassignDriverModal
        open={open}
        onOpenChange={setOpen}
        routeId={row.route_id}
        currentDriverName={row.driver_name}
        contextLabel={
          <>
            {row.name} • {row.group_name} • {formatContextDate(row.drive_date)}
          </>
        }
        onUpdated={onUpdated}
      />
    </>
  );
}
