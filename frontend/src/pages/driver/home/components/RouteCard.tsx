import { RouteMap } from '@/common/components/RouteMap';
import { Button } from '@/common/components/Button';
import { cn } from '@/lib/utils';
import type { RouteStopDetailRead } from '@/api/generated';

export interface RouteCardProps {
  title: string;
  date: string;
  encodedPolyline: string;
  stops?: RouteStopDetailRead[];
  timeRemaining?: string;
  className?: string;
}

export function RouteCard({
  title,
  date,
  encodedPolyline,
  stops,
  timeRemaining,
  className,
}: RouteCardProps) {
  // Transform RouteStopDetailRead to RouteMapStop format
  const mapStops = stops?.map((stop) => ({
    stop_number: stop.stop_number,
    latitude: stop.latitude,
    longitude: stop.longitude,
  }));

  console.log(
    'RouteCard - encodedPolyline:',
    encodedPolyline,
    'stops:',
    mapStops
  );

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
        />
        {timeRemaining && (
          <div className="absolute top-3 left-3 rounded-lg bg-blue-300/90 px-3 py-1.5 text-sm font-semibold text-white">
            {timeRemaining}
          </div>
        )}
      </div>

      {/* Details */}
      <div className="flex flex-col gap-1">
        <h3 className="text-h3 text-grey-500 font-bold">{title}</h3>
        <p className="text-p2 text-grey-500">{date}</p>
      </div>

      {/* Button */}
      <Button variant="secondary" shape="compact">
        View route
      </Button>
    </div>
  );
}
