import { useState } from 'react';

import type { LocationRead } from '@/api/generated/types.gen';
import MoreVerticalIcon from '@/assets/icons/more-vertical.svg?react';
import { Popover, PopoverContent, PopoverTrigger } from '@/common/components';
import { cn } from '@/lib/utils';

import { DeleteAddressModal } from './DeleteAddressModal';

interface AddressActionsCellProps {
  row: LocationRead;
}

/** Kebab actions cell for the Addresses tab: opens a Delete menu on click. */
export function AddressActionsCell({ row }: AddressActionsCellProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);

  return (
    <>
      <Popover open={menuOpen} onOpenChange={setMenuOpen}>
        <PopoverTrigger asChild>
          <button
            type="button"
            aria-label="Address actions"
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

      <DeleteAddressModal
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        address={row}
      />
    </>
  );
}
