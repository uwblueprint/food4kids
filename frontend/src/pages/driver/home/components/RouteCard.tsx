import { Link } from 'react-router-dom';

import type { RouteStopDetailRead } from '@/api/generated';
import { Button } from '@/common/components/Button';
import { RouteMap } from '@/common/components/RouteMap';
import { cn } from '@/lib/utils';

export interface RouteCardProps {
  title: string;
  date: string;
  encodedPolyline: string;
  stops?: RouteStopDetailRead[];
  timeRemaining?: string;
  className?: string;
  isPast?: boolean;
  routeId?: string;
}

export function RouteCard({
  title,
  date,
  encodedPolyline,
  stops,
  timeRemaining,
  className,
  isPast = false,
  routeId,
}: RouteCardProps) {
  // Transform RouteStopDetailRead to RouteMapStop format
  const mapStops = stops?.map((stop) => ({
    stop_number: stop.stop_number,
    latitude: stop.latitude,
    longitude: stop.longitude,
  }));

  // Debug logging removed: avoid console calls in production UI

  return (
    <div
      className={cn(
        'border-grey-300 flex flex-col gap-3 rounded-xl border p-4',
        className
      )}
    >
      {/* Map */}
      <div className="relative h-40 w-full">
        <RouteMap
          encodedPolyline={encodedPolyline}
          stops={mapStops}
          className="h-full w-full"
          muted={isPast}
          basemap={isPast ? 'grey' : 'default'}
        />
        {isPast && (
          // Grey overlay for past routes (non-interactive so map remains clickable)
          <div className="bg-grey-150/30 pointer-events-none absolute inset-0 z-10 rounded-[18px]" />
        )}
        {timeRemaining && (
          <div className="absolute top-3 left-3 z-20 rounded-lg bg-blue-300/90 px-3 py-1.5 text-sm font-semibold text-white">
            {timeRemaining}
          </div>
        )}
      </div>

      {/* Details */}
      <div className="flex flex-col gap-1">
        <h3 className="text-h3 text-grey-500 font-bold">{title}</h3>
        <p className="text-p2 text-grey-400">{date}</p>
      </div>

      {/* Button */}
      {routeId ? (
        <Button asChild variant="primary" shape="compact">
          <Link to={`/driver/route/${routeId}`}>View route</Link>
        </Button>
      ) : (
        <Button variant="primary" shape="compact">
          View route
        </Button>
      )}
    </div>
  );
}
