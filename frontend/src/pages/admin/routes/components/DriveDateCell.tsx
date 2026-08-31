import { useRef, useState } from 'react';

import { useUpdateRouteGroup } from '@/api/route-groups';
import {
  Calendar,
  Popover,
  PopoverContent,
  PopoverTrigger,
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/common/components';
import {
  formatShortDate,
  parseDateOnly,
  toNaiveDateString,
} from '@/common/utils';

/** How long the pointer must rest on the date before the popup opens. */
const OPEN_DELAY_MS = 400;
/** Grace period for moving the pointer from the date text into the popup. */
const CLOSE_DELAY_MS = 150;

interface DriveDateCellProps {
  /** The group whose drive_date the picked day is written to. */
  routeGroupId: string;
  /** Current drive date as the API's ISO date string. */
  driveDate: string;
  /**
   * True once any of the group's routes is frozen. The date is then part of
   * the delivery record, so the cell drops to read-only rather than offering a
   * calendar the API would reject (see RouteGroupRead.frozen).
   */
  frozen: boolean;
  /** Called once the new date saves, e.g. to highlight the updated row. */
  onUpdated?: () => void;
}

/**
 * Editable Date cell for the routes page's Groups tab: shows MM/DD/YY and
 * opens a calendar popup on hover that PATCHes the group's drive_date when a
 * day is picked.
 *
 * Groups only. The date lives on RouteGroup, so editing it from the Routes tab
 * silently moved every sibling route in the group — that tab shows the date as
 * plain text instead.
 */
export function DriveDateCell({
  routeGroupId,
  driveDate,
  frozen,
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

  const handleSelect = (date: Date | undefined) => {
    if (!date) return;
    updateRouteGroup(
      {
        path: { route_group_id: routeGroupId },
        body: { drive_date: toNaiveDateString(date) },
      },
      { onSuccess: () => onUpdated?.() }
    );
    setOpen(false);
  };

  // Say why rather than let the admin find out by being rejected: the API
  // returns 409 for this move, and a calendar that quietly fails is worse than
  // no calendar.
  if (frozen) {
    return (
      <Tooltip>
        <TooltipTrigger asChild>
          <span className="cursor-default">{formatShortDate(driveDate)}</span>
        </TooltipTrigger>
        <TooltipContent>
          These routes have been delivered — the date is part of the record and
          can no longer be changed.
        </TooltipContent>
      </Tooltip>
    );
  }

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
