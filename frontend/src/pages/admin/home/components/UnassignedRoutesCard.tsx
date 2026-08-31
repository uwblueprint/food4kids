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
          // Light ground when selected, so it takes a 1px stroke.
          isSelected &&
            'bg-blue-50 outline outline-1 outline-offset-[-1px] outline-blue-100'
        )}
      >
        <div className="flex min-w-0 flex-col">
          <p className="text-p1 text-grey-500">{route.name}</p>
          {route.group_name ? (
            <p className="text-p2 text-grey-500">{route.group_name}</p>
          ) : null}
        </div>
        <div className="flex shrink-0 flex-col text-right">
          <p className="text-p1 text-grey-500">
            {formatRouteDate(route.drive_date)}
          </p>
          <p className="text-p2 text-grey-500">{stopsLabel}</p>
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
    <Card className="shadow-admin-bento min-h-0 rounded-4xl">
      <CardHeader className="mb-4">
        <div className="flex items-start justify-between gap-2">
          <div className="flex min-w-0 items-center gap-2">
            <CardTitle className="text-h2">Unassigned</CardTitle>
            {total > 0 && (
              <Tag variant="count" className="shrink-0">
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
              className="w-[375px] shrink-0"
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
