import { useState } from 'react';

import type { RouteGroupRead } from '@/api/generated/types.gen';
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

import { DeleteRouteGroupModal } from './DeleteRouteGroupModal';
import { DuplicateRouteGroupModal } from './DuplicateRouteGroupModal';

interface RouteGroupActionsCellProps {
  row: RouteGroupRead;
  /** Called with the copy's id so the table can highlight and scroll to it. */
  onDuplicated: (routeGroupId: string) => void;
}

/**
 * Kebab actions cell for the Groups tab: opens a Duplicate/Delete menu on
 * click. Delete stays disabled until the group has no stops left.
 */
export function RouteGroupActionsCell({
  row,
  onDuplicated,
}: RouteGroupActionsCellProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [duplicateOpen, setDuplicateOpen] = useState(false);

  // Delete only once every stop has been removed from the group's routes.
  const canDelete = row.num_locations === 0;

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
            aria-label="Route group actions"
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
            className="text-p2 text-grey-500 hover:bg-grey-200 flex w-full cursor-pointer items-center rounded-lg px-3 py-2"
            onClick={() => {
              setMenuOpen(false);
              setDuplicateOpen(true);
            }}
          >
            Duplicate
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

      <DeleteRouteGroupModal
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        routeGroup={row}
      />
      <DuplicateRouteGroupModal
        open={duplicateOpen}
        onOpenChange={setDuplicateOpen}
        routeGroup={row}
        onDuplicated={onDuplicated}
      />
    </>
  );
}
