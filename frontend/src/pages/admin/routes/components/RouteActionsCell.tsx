import { useState } from 'react';

import type { RouteWithDateRead } from '@/api/generated/types.gen';
import MoreVerticalIcon from '@/assets/icons/more-vertical.svg?react';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/common/components';
import { cn } from '@/lib/utils';

import { DeleteRouteModal } from './DeleteRouteModal';
import { ReassignDriverModal } from './ReassignDriverModal';

interface RouteActionsCellProps {
  row: RouteWithDateRead;
  /** Called after an action changes the row, e.g. to highlight it. */
  onUpdated?: () => void;
}

/**
 * Kebab actions cell for the Routes tab: opens a Reassign Driver/Delete menu
 * on click. Delete stays disabled until the route has no stops left.
 */
export function RouteActionsCell({ row, onUpdated }: RouteActionsCellProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [reassignOpen, setReassignOpen] = useState(false);

  // Delete only once every stop has been removed from the route.
  const canDelete = row.num_stops === 0;

  const deleteItem = (
    <button
      type="button"
      disabled={!canDelete}
      className={cn(
        'text-p2 flex w-full items-center rounded-lg px-3 py-2',
        canDelete
          ? 'text-red hover:bg-light-red cursor-pointer'
          : 'text-grey-400 cursor-not-allowed'
      )}
      onClick={() => {
        setMenuOpen(false);
        setDeleteOpen(true);
      }}
    >
      Delete
    </button>
  );

  return (
    <>
      <Popover open={menuOpen} onOpenChange={setMenuOpen}>
        <PopoverTrigger asChild>
          <button
            type="button"
            aria-label="Route actions"
            className={cn(
              'flex size-8 cursor-pointer items-center justify-center rounded-full',
              'transition-colors hover:bg-blue-50 data-[state=open]:bg-blue-50'
            )}
          >
            <MoreVerticalIcon className="text-grey-400 size-5" />
          </button>
        </PopoverTrigger>
        <PopoverContent
          align="end"
          className="w-auto min-w-0 p-1"
          onOpenAutoFocus={(e) => e.preventDefault()}
        >
          <button
            type="button"
            className="text-p2 text-grey-500 hover:bg-grey-200 flex w-full cursor-pointer items-center rounded-lg px-3 py-2 whitespace-nowrap"
            onClick={() => {
              setMenuOpen(false);
              setReassignOpen(true);
            }}
          >
            Reassign Driver
          </button>
          {canDelete ? (
            deleteItem
          ) : (
            <Tooltip>
              {/* span wrapper so the tooltip still fires on the disabled button */}
              <TooltipTrigger asChild>
                <span>{deleteItem}</span>
              </TooltipTrigger>
              <TooltipContent side="bottom">
                Remove all stops to delete
              </TooltipContent>
            </Tooltip>
          )}
        </PopoverContent>
      </Popover>

      <DeleteRouteModal
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        route={row}
      />
      <ReassignDriverModal
        open={reassignOpen}
        onOpenChange={setReassignOpen}
        route={row}
        onUpdated={onUpdated}
      />
    </>
  );
}
