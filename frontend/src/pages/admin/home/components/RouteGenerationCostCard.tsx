import { useBillingCosts } from '@/api/billing';
import InfoCircleIcon from '@/assets/icons/info-circle.svg?react';
import {
  Card,
  CardTitle,
  Spinner,
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/common/components';

export function RouteGenerationCostCard() {
  const { data, isPending, isError, refetch, isFetching } = useBillingCosts();
  const today = new Date().toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });

  return (
    <Card className="shadow-admin-bento gap-2 rounded-4xl">
      <div className="flex items-center justify-between gap-2">
        <CardTitle>Cost of Route Generation</CardTitle>
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
              Year-to-date project spend from Cloud Billing, including credits.
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
      ) : (
        <div className="flex flex-wrap items-baseline gap-x-2">
          <p className="text-grey-500 text-2xl font-medium">
            {data.currency
              ? new Intl.NumberFormat('en-CA', {
                  style: 'currency',
                  currency: data.currency,
                  currencyDisplay: 'code',
                }).format(data.year_to_date_cost)
              : data.year_to_date_cost.toFixed(2)}
          </p>
          <p className="text-grey-400 text-xs">as of {today}</p>
        </div>
      )}
    </Card>
  );
}
