import { cn } from '@/lib/utils';

import { CURRENT_MONTH_BAR_CLASS, HISTORY_BAR_CLASSES } from './constants';
import type { CalendarMonth } from './utils';
import { formatMonthAbbreviation, formatMonthName } from './utils';

export interface MetricPoint extends CalendarMonth {
  value: number;
}

interface MonthlyMetricViewProps {
  /** Trailing months, oldest first — the last entry is the current month. */
  points: MetricPoint[];
  /** Caption under the summed figure, e.g. "Total Kilometers". */
  totalLabel: string;
  /** Renders both the summed figure and each month's value. */
  formatValue: (value: number) => string;
}

/**
 * A metric's six-month bar chart plus the two summary figures above it —
 * the shared body of the "Distance Driven" and "Deliveries Made" views.
 *
 * Bars and axis labels are two flex rows over the same `flex-1` columns and
 * gap rather than one column each, so every bar measures its height against
 * the full chart area instead of against whatever the label left over.
 */
export function MonthlyMetricView({
  points,
  totalLabel,
  formatValue,
}: MonthlyMetricViewProps) {
  const total = points.reduce((sum, point) => sum + point.value, 0);
  const peak = Math.max(...points.map((point) => point.value), 0);
  const currentMonth = points.at(-1);

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-6">
      <div className="flex items-start gap-4">
        <div className="flex flex-1 flex-col items-center gap-1">
          <p className="text-grey-500 text-3xl leading-10 font-medium">
            {formatValue(total)}
          </p>
          <p className="text-grey-400 text-base leading-5 font-light">
            {totalLabel}
          </p>
        </div>
        <div className="flex flex-1 flex-col items-center gap-1">
          <p className="text-3xl leading-10 font-semibold text-blue-300">
            {currentMonth ? formatValue(currentMonth.value) : '—'}
          </p>
          <p className="text-grey-400 text-base leading-5 font-light">
            In{' '}
            <span className="text-blue-300">
              {currentMonth ? formatMonthName(currentMonth) : ''}
            </span>
          </p>
        </div>
      </div>

      <div className="flex min-h-0 flex-1 flex-col gap-1">
        <div className="flex min-h-0 flex-1 items-end gap-4">
          {points.map((point, index) => (
            <div
              key={`${point.year}-${point.month}`}
              className="flex h-full flex-1 items-end"
            >
              <div
                // A month with no activity draws nothing; anything above zero
                // keeps a sliver so it can't be mistaken for one that has none.
                className={cn(
                  'w-full rounded-lg',
                  point.value > 0 && 'min-h-1',
                  index === points.length - 1
                    ? CURRENT_MONTH_BAR_CLASS
                    : HISTORY_BAR_CLASSES[index % HISTORY_BAR_CLASSES.length]
                )}
                style={{
                  height: peak > 0 ? `${(point.value / peak) * 100}%` : 0,
                }}
                role="img"
                aria-label={`${formatMonthName(point)}: ${formatValue(point.value)}`}
              />
            </div>
          ))}
        </div>
        <div className="flex gap-4">
          {points.map((point) => (
            <p
              key={`${point.year}-${point.month}`}
              aria-hidden
              className="text-grey-400 flex-1 text-center text-base font-light"
            >
              {formatMonthAbbreviation(point)}
            </p>
          ))}
        </div>
      </div>
    </div>
  );
}
