import { useRef, useState } from 'react';

import { useUpdateRouteGroup } from '@/api/route-groups';
import {
  Calendar,
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/common/components';
import { formatShortDate, parseDateOnly } from '@/common/utils';

/** How long the pointer must rest on the date before the popup opens. */
const OPEN_DELAY_MS = 400;
/** Grace period for moving the pointer from the date text into the popup. */
const CLOSE_DELAY_MS = 150;

interface DriveDateCellProps {
  /** The group whose drive_date the picked day is written to. */
  routeGroupId: string;
  /** Current drive date as the API's naive ISO datetime string. */
  driveDate: string;
  /** Called once the new date saves, e.g. to highlight the updated row. */
  onUpdated?: () => void;
}

/**
 * Date cell for the routes-page tables: shows MM/DD/YY and opens a calendar
 * popup on hover that PATCHes the group's drive_date when a day is picked.
 * On the Routes tab this moves the whole group the route belongs to (the
 * date lives on the group, so sibling routes move with it).
 */
export function DriveDateCell({
  routeGroupId,
  driveDate,
  onUpdated,
}: DriveDateCellProps) {
  const [open, setOpen] = useState(false);
  const hoverTimer = useRef<ReturnType<typeof setTimeout> | undefined>(
    undefined
  );
  const { mutate: updateRouteGroup } = useUpdateRouteGroup();

  // While open, re-entering the trigger or popup only cancels a pending
  // close; the open delay applies just to the initial hover.
  const hoverOpen = () => {
    clearTimeout(hoverTimer.current);
    if (!open) {
      hoverTimer.current = setTimeout(() => setOpen(true), OPEN_DELAY_MS);
    }
  };
  const hoverClose = () => {
    clearTimeout(hoverTimer.current);
    hoverTimer.current = setTimeout(() => setOpen(false), CLOSE_DELAY_MS);
  };

  const selected = parseDateOnly(driveDate);
  // drive_date is a naive datetime; keep its time-of-day, change only the day
  const [, timePart = '00:00:00'] = driveDate.split('T');

  const handleSelect = (date: Date | undefined) => {
    if (!date) return;
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const d = String(date.getDate()).padStart(2, '0');
    updateRouteGroup(
      {
        path: { route_group_id: routeGroupId },
        body: { drive_date: `${y}-${m}-${d}T${timePart}` },
      },
      { onSuccess: () => onUpdated?.() }
    );
    setOpen(false);
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button
          type="button"
          onMouseEnter={hoverOpen}
          onMouseLeave={hoverClose}
          className="-mx-1.5 cursor-pointer rounded-md px-1.5 py-1 transition-colors hover:bg-blue-50 data-[state=open]:bg-blue-50"
        >
          {formatShortDate(driveDate)}
        </button>
      </PopoverTrigger>
      <PopoverContent
        align="start"
        className="w-auto p-0"
        onOpenAutoFocus={(e) => e.preventDefault()}
        onMouseEnter={hoverOpen}
        onMouseLeave={hoverClose}
      >
        <Calendar
          mode="single"
          selected={selected}
          onSelect={handleSelect}
          defaultMonth={selected}
          classNames={{
            // Match the mock: caption on the left, both chevrons on the right
            month_caption: 'flex h-(--cell-size) items-center pl-1',
            nav: 'absolute top-0 right-0 flex items-center gap-1',
          }}
        />
      </PopoverContent>
    </Popover>
  );
}
