import { useState } from 'react';

import { useMonthlyDriverRanking, useMonthlySeries } from '@/api/reports';
import ArrowDropDownIcon from '@/assets/icons/arrow-drop-down.svg?react';
import {
  Card,
  Popover,
  PopoverContent,
  PopoverTrigger,
  Spinner,
} from '@/common/components';
import { cn } from '@/lib/utils';

import type { StatisticView } from './constants';
import { SERIES_MONTHS, STATISTIC_VIEWS } from './constants';
import { MonthlyMetricView } from './MonthlyMetricView';
import { MonthStepper } from './MonthStepper';
import { TopDriversView } from './TopDriversView';
import type { CalendarMonth } from './utils';
import {
  formatCount,
  formatKilometres,
  isSameMonth,
  shiftMonth,
} from './utils';

/**
 * The homepage's toggleable statistics card: one bento tile whose title is a
 * dropdown switching between distance driven, deliveries made, and the
 * month's top drivers.
 *
 * The two bar-chart views read from a single six-month series request, so
 * toggling between them is instant and costs no extra fetch. "Top Drivers" is
 * a separate per-month request, issued only once that view is opened.
 */
export function StatisticsWidget() {
  const [view, setView] = useState<StatisticView>('distance');
  const [menuOpen, setMenuOpen] = useState(false);
  // Only Top Drivers is month-scoped; null means "follow the series' newest
  // month", which keeps the widget correct across a month boundary without
  // trusting the browser clock to agree with the backend's timezone.
  const [rankingMonth, setRankingMonth] = useState<CalendarMonth | null>(null);

  const { data: series, isLoading, isError } = useMonthlySeries(SERIES_MONTHS);

  const latest = series?.at(-1);
  const newestMonth: CalendarMonth | undefined = latest
    ? { year: latest.year, month: latest.month }
    : undefined;
  const selectedMonth = rankingMonth ?? newestMonth;

  const { data: rankings = [], isLoading: isRankingLoading } =
    useMonthlyDriverRanking(view === 'drivers' ? selectedMonth : undefined);

  const activeView = STATISTIC_VIEWS.find(({ id }) => id === view);
  const hasSeries = series !== undefined && series.length > 0;

  const renderBody = () => {
    if (isLoading) {
      return (
        <div className="flex flex-1 items-center justify-center">
          <Spinner />
        </div>
      );
    }

    if (isError || !hasSeries || !selectedMonth) {
      return (
        <div className="flex flex-1 items-center justify-center">
          <p className="text-grey-400 text-p1 text-center">
            Statistics couldn’t be loaded right now.
          </p>
        </div>
      );
    }

    if (view === 'drivers') {
      return (
        <TopDriversView
          rankings={rankings}
          isLoading={isRankingLoading}
          month={selectedMonth}
        />
      );
    }

    const isDistance = view === 'distance';
    return (
      <MonthlyMetricView
        points={series.map((point) => ({
          year: point.year,
          month: point.month,
          value: isDistance ? point.total_km : point.total_deliveries,
        }))}
        totalLabel={isDistance ? 'Total Kilometers' : 'Total Deliveries'}
        formatValue={isDistance ? formatKilometres : formatCount}
      />
    );
  };

  return (
    // The bar chart sizes its columns against the card, and the card is the
    // shorter tile in the homepage's right-hand stack — so it states a height
    // rather than taking one from its content. It also keeps the tile from
    // resizing as the user toggles between the three views.
    <Card className="shadow-admin-bento min-h-[327px] gap-4 rounded-4xl">
      {/* Title and month stepper share this row, per the Top Drivers design. */}
      <div className="flex items-center justify-between gap-4">
        <Popover open={menuOpen} onOpenChange={setMenuOpen}>
          <PopoverTrigger asChild>
            <button
              type="button"
              aria-label="Change statistic"
              className="flex cursor-pointer items-center gap-1 rounded-sm focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-blue-300"
            >
              <span className="font-nunito text-h2 text-grey-500 font-bold">
                {activeView?.label}
              </span>
              <ArrowDropDownIcon
                className={cn(
                  'text-grey-500 size-6 transition-transform',
                  menuOpen && 'rotate-180'
                )}
              />
            </button>
          </PopoverTrigger>
          <PopoverContent
            align="start"
            sideOffset={8}
            className="border-grey-200 w-44 border p-3 shadow-[0px_0px_12px_rgba(0,0,0,0.08)]"
          >
            <div className="flex flex-col">
              {STATISTIC_VIEWS.map(({ id, label }) => (
                <button
                  key={id}
                  type="button"
                  onClick={() => {
                    setView(id);
                    setMenuOpen(false);
                  }}
                  className={cn(
                    'text-p1 text-grey-500 cursor-pointer rounded-sm p-2 text-left transition-colors hover:bg-blue-50 focus-visible:outline-2 focus-visible:outline-blue-300',
                    id === view && 'bg-blue-50'
                  )}
                >
                  {label}
                </button>
              ))}
            </div>
          </PopoverContent>
        </Popover>

        {view === 'drivers' && selectedMonth && newestMonth && (
          <MonthStepper
            month={selectedMonth}
            onStep={(offset) =>
              setRankingMonth(shiftMonth(selectedMonth, offset))
            }
            canStepForward={!isSameMonth(selectedMonth, newestMonth)}
          />
        )}
      </div>

      {renderBody()}
    </Card>
  );
}
