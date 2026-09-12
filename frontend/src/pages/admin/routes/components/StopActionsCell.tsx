import { useState } from 'react';

import MoreVerticalIcon from '@/assets/icons/more-vertical.svg?react';
import { Popover, PopoverContent, PopoverTrigger } from '@/common/components';
import { cn } from '@/lib/utils';

import { MoveStopModal } from './MoveStopModal';
import { RemoveStopModal } from './RemoveStopModal';

interface StopActionsCellProps {
  routeId: string;
  /** Route name, shown in the delete confirmation copy. */
  routeName: string;
  routeGroupId: string;
  /** The route's current stops in order, as location ids. */
  locationIds: string[];
  stopLocationId: string;
  stopAddress: string;
}

/** Kebab menu for a stop row: move to another route, or remove. */
export function StopActionsCell({
  routeId,
  routeName,
  routeGroupId,
  locationIds,
  stopLocationId,
  stopAddress,
}: StopActionsCellProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [moveOpen, setMoveOpen] = useState(false);
  const [removeOpen, setRemoveOpen] = useState(false);

  return (
    <>
      <Popover open={menuOpen} onOpenChange={setMenuOpen}>
        <PopoverTrigger asChild>
          <button
            type="button"
            aria-label="Stop actions"
            className={cn(
              'flex size-8 cursor-pointer items-center justify-center rounded-full',
              'transition-colors hover:bg-blue-50 data-[state=open]:bg-blue-50'
            )}
          >
            <MoreVerticalIcon className="text-grey-500 size-5" />
          </button>
        </PopoverTrigger>
        {/* Figma stop menu: 16px-radius container clipping items that are each
            their own bordered frame — 48px tall, 16px horizontal padding
            (6px outer + 10px inner frame), 1px Grey-200 border, white bg. The
            shared border between stacked items collapses to a crisp 1px (via
            -mt-px), which reads as the divider. Width hugs the widest item. */}
        <PopoverContent
          align="end"
          className="w-fit min-w-0 overflow-hidden rounded-2xl p-0"
          onOpenAutoFocus={(e) => e.preventDefault()}
        >
          <button
            type="button"
            className="border-grey-200 bg-grey-100 text-p2 text-grey-500 hover:bg-grey-200 flex h-12 w-full cursor-pointer items-center border px-4 whitespace-nowrap"
            onClick={() => {
              setMenuOpen(false);
              setMoveOpen(true);
            }}
          >
            Transfer stop
          </button>
          <button
            type="button"
            className="border-grey-200 bg-grey-100 text-p2 text-red hover:bg-light-red -mt-px flex h-12 w-full cursor-pointer items-center border px-4 whitespace-nowrap"
            onClick={() => {
              setMenuOpen(false);
              setRemoveOpen(true);
            }}
          >
            Delete
          </button>
        </PopoverContent>
      </Popover>

      <RemoveStopModal
        open={removeOpen}
        onOpenChange={setRemoveOpen}
        routeId={routeId}
        routeName={routeName}
        locationIds={locationIds}
        stopLocationId={stopLocationId}
        stopAddress={stopAddress}
      />
      <MoveStopModal
        open={moveOpen}
        onOpenChange={setMoveOpen}
        sourceRouteId={routeId}
        sourceRouteGroupId={routeGroupId}
        locationIds={locationIds}
        stopLocationId={stopLocationId}
        stopAddress={stopAddress}
      />
    </>
  );
}
