import { useState } from 'react';
import { Link } from 'react-router-dom';

import type { RouteWithDateRead } from '@/api/generated/types.gen';
import { Button, Spinner } from '@/common/components';
import { RouteMap } from '@/common/components/RouteMap';
import { useRoute } from '@/common/hooks/useRoute';
import { parseDateOnly } from '@/common/utils';
import { cn } from '@/lib/utils';

import { ReassignDriverModal } from '../../routes/components/ReassignDriverModal';

interface UnassignedRoutePreviewCardProps {
  route: RouteWithDateRead;
  className?: string;
}

function formatPreviewDate(driveDate: string): string {
  return parseDateOnly(driveDate).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  });
}

function formatStartTime(value: string | null | undefined): string | null {
  if (!value) return null;
  const [h, m] = value.split(':');
  const hour = Number(h);
  const minute = Number(m);
  if (Number.isNaN(hour) || Number.isNaN(minute)) return null;
  const period = hour < 12 ? 'AM' : 'PM';
  const hour12 = hour % 12 === 0 ? 12 : hour % 12;
  return `${hour12}:${String(minute).padStart(2, '0')} ${period}`;
}

function PreviewMetadata({ route }: { route: RouteWithDateRead }) {
  const parts = [
    formatPreviewDate(route.drive_date),
    formatStartTime(route.start_time),
    `${route.num_stops} stop${route.num_stops === 1 ? '' : 's'}`,
  ].filter(Boolean);

  return <p className="text-p2 text-grey-400">{parts.join(' • ')}</p>;
}

export function UnassignedRoutePreviewCard({
  route,
  className,
}: UnassignedRoutePreviewCardProps) {
  const { data: detail, isLoading, isError } = useRoute(route.route_id);
  const [assignOpen, setAssignOpen] = useState(false);

  return (
    <>
      <div
        className={cn(
          'isolate z-0 flex min-w-0 flex-col items-start self-stretch',
          className
        )}
      >
        <div className="outline-grey-300 flex w-full flex-col overflow-hidden rounded-xl bg-white outline outline-1 outline-offset-[-1px]">
          <div className="bg-grey-150 relative isolate z-0 h-[162px] w-full shrink-0 overflow-hidden [&_.leaflet-bottom]:z-0 [&_.leaflet-container]:z-0 [&_.leaflet-pane]:z-0 [&_.leaflet-top]:z-0">
            {isLoading && (
              <div className="absolute inset-0 z-10 flex items-center justify-center">
                <Spinner size="sm" />
              </div>
            )}
            {!isLoading && !isError && (
              <div className="pointer-events-none h-full w-full">
                <RouteMap
                  key={route.route_id}
                  encodedPolyline={detail?.encoded_polyline}
                  stops={detail?.stops}
                  className="h-full rounded-none border-0"
                />
              </div>
            )}
            {!isLoading && isError && (
              <div className="text-m-p3 text-grey-400 flex h-full items-center justify-center px-4 text-center">
                Map unavailable
              </div>
            )}
          </div>

          <div className="flex flex-col gap-4 self-stretch px-4 pt-2 pb-4">
            <div className="flex flex-col gap-1">
              <p className="text-h3 text-grey-500 font-bold">{route.name}</p>
              <PreviewMetadata route={route} />
            </div>
            <div className="flex items-center gap-4 self-stretch">
              <Button variant="secondary" asChild className="min-w-0 flex-1">
                <Link to="/admin/routes?tab=routes">View route</Link>
              </Button>
              <Button
                variant="primary"
                className="min-w-0 flex-1"
                onClick={() => setAssignOpen(true)}
              >
                Assign
              </Button>
            </div>
          </div>
        </div>
      </div>

      <ReassignDriverModal
        open={assignOpen}
        onOpenChange={setAssignOpen}
        routeId={route.route_id}
        currentDriverName={route.driver_name}
        contextLabel={
          <>
            {route.name} • {route.group_name} •{' '}
            {formatPreviewDate(route.drive_date)}
          </>
        }
      />
    </>
  );
}
