import { useRef, useState } from 'react';

import { useUpdateRouteGroup } from '@/api/route-groups';
import {
  Calendar,
  ConfirmModal,
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/common/components';
import {
  formatShortDate,
  isPastDate,
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
  onUpdated,
}: DriveDateCellProps) {
  const [open, setOpen] = useState(false);
  const [pendingPastDate, setPendingPastDate] = useState<Date | undefined>(
    undefined
  );
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

  const save = (date: Date) => {
    updateRouteGroup(
      {
        path: { route_group_id: routeGroupId },
        body: { drive_date: toNaiveDateString(date) },
      },
      { onSuccess: () => onUpdated?.() }
    );
  };

  // Moving an upcoming group back past today makes it due for tonight's
  // freeze, which writes it into driver history. Allowed, but confirmed
  // first. Shuffling an already-past group between past dates introduces
  // nothing new, so it saves straight through.
  const handleSelect = (date: Date | undefined) => {
    if (!date) return;
    setOpen(false);
    if (isPastDate(date) && !isPastDate(selected)) {
      setPendingPastDate(date);
      return;
    }
    save(date);
  };

  return (
    <>
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

      <ConfirmModal
        open={pendingPastDate !== undefined}
        onOpenChange={(next) => {
          if (!next) setPendingPastDate(undefined);
        }}
        onConfirm={() => {
          if (pendingPastDate) save(pendingPastDate);
          setPendingPastDate(undefined);
        }}
        title="Move to a past date?"
        description={
          pendingPastDate
            ? `${formatShortDate(toNaiveDateString(pendingPastDate))} has already passed, so tonight's nightly job will record this group as a completed delivery and count it in driver history.`
            : ''
        }
        confirmLabel="Move anyway"
      />
    </>
  );
}
