import { useState } from 'react';

import type { RouteGroupRead } from '@/api/generated/types.gen';
import MoreVerticalIcon from '@/assets/icons/more-vertical.svg?react';
import { Popover, PopoverContent, PopoverTrigger } from '@/common/components';
import { cn } from '@/lib/utils';

import { DeleteRouteModal } from './DeleteRouteModal';
import { DuplicateRouteGroupModal } from './DuplicateRouteGroupModal';

interface RouteGroupActionsCellProps {
  row: RouteGroupRead;
  /** Called with the copy's id so the table can highlight and scroll to it. */
  onDuplicated: (routeGroupId: string) => void;
}

export function RouteGroupActionsCell({
  row,
  onDuplicated,
}: RouteGroupActionsCellProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [duplicateOpen, setDuplicateOpen] = useState(false);

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
            <MoreVerticalIcon className="text-grey-400 size-4" />
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
          <button
            type="button"
            className="text-p2 text-red hover:bg-light-red flex w-full cursor-pointer items-center rounded-lg px-3 py-2"
            onClick={() => {
              setMenuOpen(false);
              setDeleteOpen(true);
            }}
          >
            Delete
          </button>
        </PopoverContent>
      </Popover>

      {deleteOpen && (
        <DeleteRouteModal
          onClose={() => setDeleteOpen(false)}
          kind="route group"
          id={row.route_group_id}
          name={row.name}
        />
      )}
      <DuplicateRouteGroupModal
        open={duplicateOpen}
        onOpenChange={setDuplicateOpen}
        routeGroup={row}
        onDuplicated={onDuplicated}
      />
    </>
  );
}
