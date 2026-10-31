import type { ReactNode } from 'react';

import {
  Button,
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/common/components';

interface BlockedButtonProps {
  children: ReactNode;
  onClick?: () => void;
  /** Why the button is unavailable, or null when it is. */
  blockedReason: string | null;
  disabled?: boolean;
  className?: string;
}

/**
 * A button that explains itself when it is unavailable.
 *
 * A disabled button swallows pointer events, so the tooltip has to hang off a
 * wrapper element rather than the button -- which is why it stays mounted
 * while blocked instead of being swapped out.
 */
export const BlockedButton = ({
  children,
  onClick,
  blockedReason,
  disabled,
  className,
}: BlockedButtonProps) => {
  const button = (
    <Button
      onClick={onClick}
      disabled={disabled || blockedReason !== null}
      className={className}
    >
      {children}
    </Button>
  );

  if (!blockedReason) return button;

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span className={className}>{button}</span>
      </TooltipTrigger>
      <TooltipContent className="bg-grey-500 text-grey-100">
        {blockedReason}
      </TooltipContent>
    </Tooltip>
  );
};
