import ChevronLeftIcon from '@/assets/icons/chevron-left.svg?react';
import ChevronRightIcon from '@/assets/icons/chevron-right.svg?react';

import type { CalendarMonth } from './utils';
import { formatMonthName } from './utils';

interface MonthStepperProps {
  month: CalendarMonth;
  onStep: (offset: number) => void;
  /** Blocks stepping past the newest month with data. */
  canStepForward: boolean;
}

/**
 * The named month plus its back/forward arrows.
 *
 * Lives in the card header rather than inside the view it drives, so it sits
 * on the title's line the way the design has it.
 */
export function MonthStepper({
  month,
  onStep,
  canStepForward,
}: MonthStepperProps) {
  return (
    <div className="flex items-center gap-2">
      <p className="text-grey-400 text-base leading-6 font-bold">
        {formatMonthName(month)}
      </p>
      <div className="flex items-center">
        <button
          type="button"
          aria-label="Previous month"
          onClick={() => onStep(-1)}
          className="text-grey-400 hover:bg-grey-200 cursor-pointer rounded-full transition-colors focus-visible:outline-2 focus-visible:outline-blue-300"
        >
          <ChevronLeftIcon className="size-6" />
        </button>
        <button
          type="button"
          aria-label="Next month"
          onClick={() => onStep(1)}
          disabled={!canStepForward}
          className="text-grey-400 hover:bg-grey-200 cursor-pointer rounded-full transition-colors focus-visible:outline-2 focus-visible:outline-blue-300 disabled:pointer-events-none disabled:opacity-40"
        >
          <ChevronRightIcon className="size-6" />
        </button>
      </div>
    </div>
  );
}
