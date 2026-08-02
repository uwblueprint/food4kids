import { useState } from 'react';

import type { RouteWithDateRead } from '@/api/generated/types.gen';
import { Button } from '@/common/components';

import { ReassignDriverModal } from './ReassignDriverModal';

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
        route={row}
        onUpdated={onUpdated}
      />
    </>
  );
}
