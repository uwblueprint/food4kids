import { useState } from 'react';

import { useBillingCosts } from '@/api/billing';
import ArrowDropDownIcon from '@/assets/icons/arrow-drop-down.svg?react';
import InfoCircleIcon from '@/assets/icons/info-circle.svg?react';
import {
  Card,
  CardTitle,
  Popover,
  PopoverContent,
  PopoverTrigger,
  Progress,
  Spinner,
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/common/components';
import { cn } from '@/lib/utils';

const COST_VIEWS = [
  { id: 'all_time_cost', label: 'All Time' },
  { id: 'year_to_date_cost', label: 'Year to Date' },
  { id: 'gross_cost', label: 'Month to Date' },
] as const;

function formatCost(value: number, currency: string) {
  return currency
    ? new Intl.NumberFormat('en-CA', {
        style: 'currency',
        currency,
        currencyDisplay: 'code',
      }).format(value)
    : value.toFixed(2);
}

export function RouteGenerationCostCard() {
  const [view, setView] =
    useState<(typeof COST_VIEWS)[number]['id']>('year_to_date_cost');
  const [menuOpen, setMenuOpen] = useState(false);
  const { data, isPending, isError, refetch, isFetching } = useBillingCosts();
  const today = new Date().toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });

  const activeLabel = COST_VIEWS.find(({ id }) => id === view)?.label;
  const monthly = view === 'gross_cost';
  const currency = data?.currency || (monthly ? 'CAD' : '');
  const allowance = data?.monthly_credit_allowance ?? 0;
  const showAllowance = monthly && allowance > 0;
  const grossCost = data?.gross_cost ?? 0;
  const cost = data?.[view];
  const allowanceUsed = showAllowance
    ? Math.min(100, Math.max(0, (grossCost / allowance) * 100))
    : 0;
  const resetsOn = data
    ? new Date(`${data.invoice_month}-01T00:00:00Z`)
    : undefined;
  resetsOn?.setUTCMonth(resetsOn.getUTCMonth() + 1);

  return (
    <Card className="shadow-admin-bento gap-2 rounded-4xl py-3">
      <div className="flex items-center justify-between gap-2">
        <Popover open={menuOpen} onOpenChange={setMenuOpen}>
          <CardTitle>
            <PopoverTrigger asChild>
              <button
                type="button"
                aria-label={`Change route generation cost view, ${activeLabel}`}
                className="flex cursor-pointer items-center gap-1 rounded-sm focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-blue-300"
              >
                {activeLabel}
                <ArrowDropDownIcon
                  className={cn(
                    'text-grey-500 size-6 transition-transform',
                    menuOpen && 'rotate-180'
                  )}
                />
              </button>
            </PopoverTrigger>
          </CardTitle>
          <PopoverContent
            align="start"
            sideOffset={3}
            className="shadow-dropdown flex w-[175px] flex-col rounded-xl p-3"
          >
            {COST_VIEWS.map(({ id, label }) => (
              <button
                key={id}
                type="button"
                aria-pressed={id === view}
                onClick={() => {
                  setView(id);
                  setMenuOpen(false);
                }}
                className={cn(
                  'text-grey-500 cursor-pointer rounded-sm p-2 text-left text-base leading-[22px] transition-colors hover:bg-blue-50 focus-visible:outline-2 focus-visible:outline-blue-300',
                  id === view && 'bg-blue-50'
                )}
              >
                {label}
              </button>
            ))}
          </PopoverContent>
        </Popover>
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              type="button"
              aria-label="About route generation cost"
              className="text-grey-400 rounded-full focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-300"
            >
              <InfoCircleIcon className="size-5" />
            </button>
          </TooltipTrigger>
          <TooltipContent className="max-w-xs">
            <p>
              {monthly
                ? 'Monthly project spend before credits, based on the current billing month.'
                : 'Project spend from Cloud Billing after credits.'}{' '}
              Billing data can be delayed by several hours.
            </p>
            {data?.data_as_of && (
              <p>
                Last updated:{' '}
                {new Date(data.data_as_of).toLocaleString('en-US')}
              </p>
            )}
          </TooltipContent>
        </Tooltip>
      </div>
      {isPending ? (
        <Spinner size="xs" />
      ) : isError || !data ? (
        <div
          className="text-grey-400 text-p2 flex items-center gap-2"
          role="status"
        >
          <span>Cost unavailable.</span>
          <button
            type="button"
            className="cursor-pointer text-blue-300 underline"
            disabled={isFetching}
            onClick={() => void refetch()}
          >
            Retry
          </button>
        </div>
      ) : cost == null ? (
        <p className="text-grey-400 text-p2" role="status">
          Cost unavailable.
        </p>
      ) : showAllowance ? (
        <div className="flex flex-col gap-1 text-right">
          <p className="text-grey-500 text-xl font-medium">
            {formatCost(grossCost, currency)} / {allowance.toFixed(2)}
          </p>
          <Progress
            aria-label="Monthly free credits used"
            aria-valuetext={`${formatCost(Math.max(0, allowance - grossCost), currency)} remaining`}
            value={allowanceUsed}
            className={cn(
              allowanceUsed === 100 &&
                '[&_[data-slot=progress-indicator]]:bg-red'
            )}
          />
          <p className="text-grey-400 text-xs">
            Resets on{' '}
            {resetsOn?.toLocaleDateString('en-US', {
              month: 'short',
              day: 'numeric',
              year: 'numeric',
              timeZone: 'UTC',
            })}
          </p>
        </div>
      ) : (
        <div className="flex flex-wrap items-baseline gap-x-2">
          <p className="text-grey-500 text-2xl font-medium">
            {formatCost(cost, currency)}
          </p>
          <p className="text-grey-400 text-xs">
            {view === 'year_to_date_cost' ? 'YTD ' : ''}as of {today}
          </p>
        </div>
      )}
    </Card>
  );
}
