import type { ReactNode } from 'react';

import InfoCircleIcon from '@/assets/icons/info-circle.svg?react';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/common/components';

/**
 * "Status" column header with an info tooltip. Placed inside the DataTable's
 * sortable header button, so clicking anywhere (including the info icon) also
 * toggles the sort; the tooltip itself opens on hover/focus.
 */
export function StatusHeader({ children }: { children: ReactNode }) {
  return (
    <span className="flex items-center gap-1.5">
      Status
      <Tooltip>
        <TooltipTrigger asChild>
          <InfoCircleIcon className="size-4 cursor-pointer" />
        </TooltipTrigger>
        <TooltipContent>{children}</TooltipContent>
      </Tooltip>
    </span>
  );
}
