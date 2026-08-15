import TrophyIcon from '@/assets/icons/trophy.svg?react';
import { Spinner } from '@/common/components';

import { TOP_DRIVERS_LIMIT } from './constants';
import type { CalendarMonth } from './utils';
import { formatKilometres, formatMonthName } from './utils';

interface DriverRanking {
  driver_id: string;
  driver_name: string;
  km: number;
}

interface TopDriversViewProps {
  rankings: DriverRanking[];
  isLoading: boolean;
  /** Only for naming the month in the empty state — the stepper that changes
   * it lives in the card header, on the title's line. */
  month: CalendarMonth;
}

/**
 * Drivers ranked by kilometres driven in a single month, with the leader
 * called out and the rest listed as a numbered runner-up list.
 */
export function TopDriversView({
  rankings,
  isLoading,
  month,
}: TopDriversViewProps) {
  const [leader, ...runnersUp] = rankings.slice(0, TOP_DRIVERS_LIMIT);

  if (isLoading) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <Spinner />
      </div>
    );
  }

  if (rankings.length === 0) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <p className="text-grey-400 text-p1 text-center">
          No driving recorded in {formatMonthName(month)}.
        </p>
      </div>
    );
  }

  return (
    <ol className="flex min-h-0 flex-1 flex-col gap-4">
      <li className="flex h-16 items-center justify-between rounded-lg bg-blue-50 p-3">
        <div className="flex items-center gap-2">
          <span className="flex size-10 shrink-0 items-center justify-center rounded-full bg-blue-300">
            <TrophyIcon className="size-[18px] text-blue-50" />
          </span>
          <span className="text-base leading-5 font-extrabold text-blue-300">
            {leader.driver_name}
          </span>
        </div>
        <span className="text-base leading-5 font-extrabold text-blue-300">
          {formatKilometres(leader.km)}km
        </span>
      </li>
      {runnersUp.map((driver, index) => (
        <li
          key={driver.driver_id}
          className="flex flex-1 items-center justify-between pr-3 text-base leading-5 font-light"
        >
          <span className="text-grey-500">
            {index + 2}. {driver.driver_name}
          </span>
          <span className="text-grey-400">{formatKilometres(driver.km)}km</span>
        </li>
      ))}
    </ol>
  );
}
