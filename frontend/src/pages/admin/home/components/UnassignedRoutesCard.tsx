import { useState } from 'react';
import { Link } from 'react-router-dom';

import type { RouteWithDateRead } from '@/api/generated/types.gen';
import { useRoutes } from '@/api/routes';
import {
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Spinner,
  Tag,
} from '@/common/components';
import { parseDateOnly, toNaiveDateString } from '@/common/utils';
import { cn } from '@/lib/utils';

import { UnassignedRoutePreviewCard } from './UnassignedRoutePreviewCard';

const WIDGET_PAGE_SIZE = 5;

function formatRouteDate(driveDate: string): string {
  return parseDateOnly(driveDate).toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  });
}

function routeKey(route: RouteWithDateRead): string {
  return `${route.route_id}-${route.drive_date}`;
}

function UnassignedRouteRow({
  route,
  isSelected,
  onSelect,
}: {
  route: RouteWithDateRead;
  isSelected: boolean;
  onSelect: () => void;
}) {
  const stopsLabel = `${route.num_stops} stop${route.num_stops === 1 ? '' : 's'}`;

  return (
    <li>
      <button
        type="button"
        onClick={onSelect}
        className={cn(
          'flex w-full cursor-pointer items-center justify-between self-stretch rounded-sm px-5 py-2 text-left',
          isSelected && 'bg-blue-50'
        )}
      >
        <div className="flex min-w-0 flex-col">
          <p className="text-m-p2 text-grey-500 font-normal">{route.name}</p>
          {route.group_name ? (
            <p className="text-m-p3 text-grey-500 font-normal">
              {route.group_name}
            </p>
          ) : null}
        </div>
        <div className="flex shrink-0 flex-col text-right">
          <p className="text-m-p2 text-grey-500 font-normal">
            {formatRouteDate(route.drive_date)}
          </p>
          <p className="text-m-p3 text-grey-500 font-normal">{stopsLabel}</p>
        </div>
      </button>
    </li>
  );
}

export function UnassignedRoutesCard() {
  const today = toNaiveDateString(new Date());
  const { data, isLoading, isError } = useRoutes({
    unassigned_only: true,
    start_date: today,
    order: 'asc',
    page: 1,
    page_size: WIDGET_PAGE_SIZE,
  });
  const [selectedKey, setSelectedKey] = useState<string | null>(null);

  const routes: RouteWithDateRead[] = data?.items ?? [];
  const total = data?.total ?? 0;

  const effectiveSelectedKey =
    selectedKey && routes.some((route) => routeKey(route) === selectedKey)
      ? selectedKey
      : routes[0]
        ? routeKey(routes[0])
        : null;
  const selectedRoute =
    routes.find((route) => routeKey(route) === effectiveSelectedKey) ?? null;

  return (
    <Card className="col-span-2 min-h-0">
      <CardHeader className="mb-2">
        <div className="flex items-center justify-between gap-2">
          <div className="flex min-w-0 items-center gap-2">
            <CardTitle className="text-h3">Unassigned</CardTitle>
            {total > 0 && (
              <Tag variant="error" className="shrink-0">
                {total} route{total === 1 ? '' : 's'}
              </Tag>
            )}
          </div>
          <Button variant="textLink" asChild className="shrink-0">
            <Link to="/admin/routes?tab=routes">View all</Link>
          </Button>
        </div>
      </CardHeader>
      <CardContent className="flex min-h-0 flex-col gap-3">
        {isLoading && (
          <div className="flex flex-1 items-center justify-center py-8">
            <Spinner size="sm" />
          </div>
        )}

        {!isLoading && isError && (
          <p className="text-p2 text-grey-400 py-6 text-center">
            Couldn&apos;t load unassigned routes. Try refreshing.
          </p>
        )}

        {!isLoading && !isError && routes.length === 0 && (
          <p className="text-p2 text-grey-400 py-6 text-center">
            All upcoming routes have drivers assigned.
          </p>
        )}

        {!isLoading && !isError && routes.length > 0 && selectedRoute && (
          <div className="flex min-h-0 gap-4">
            <UnassignedRoutePreviewCard
              route={selectedRoute}
              className="min-w-0"
            />
            <ul className="flex min-h-0 min-w-0 flex-1 flex-col gap-1 overflow-y-auto">
              {routes.map((route) => {
                const key = routeKey(route);
                return (
                  <UnassignedRouteRow
                    key={key}
                    route={route}
                    isSelected={effectiveSelectedKey === key}
                    onSelect={() => setSelectedKey(key)}
                  />
                );
              })}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
