import { ChevronLeft, Map, MapPin, Package, Users } from 'lucide-react';
import { useState } from 'react';
import { Link } from 'react-router-dom';

import { getGoogleMapsLink } from '@/api/generated';
import { Button, Spinner } from '@/common/components';
import { RouteMap } from '@/common/components/RouteMap';
import { useRoute } from '@/common/hooks/useRoute';
import { cn } from '@/lib/utils';

import { RouteStopCard } from './RouteStopCard';

// TODO: replace with the real Food4Kids office number
const F4K_PHONE = '+1-555-0100';

const statusWrapper =
  'flex w-full items-center justify-center rounded-2xl border border-grey-300 bg-grey-150 p-8';

export interface RouteDetailViewProps {
  routeId: string;
  className?: string;
}

/** Format a date-time string as e.g. "Oct 18" (no year, per design). */
function formatDriveDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  });
}

/** Format a time-of-day string ("08:00:00") as "8:00AM". */
function formatStartTime(value: string | null | undefined): string | null {
  if (!value) return null;
  const [h, m] = value.split(':');
  const hour = Number(h);
  const minute = Number(m);
  if (Number.isNaN(hour) || Number.isNaN(minute)) return null;
  const period = hour < 12 ? 'AM' : 'PM';
  const hour12 = hour % 12 === 0 ? 12 : hour % 12;
  return `${hour12}:${String(minute).padStart(2, '0')}${period}`;
}

export function RouteDetailView({ routeId, className }: RouteDetailViewProps) {
  const { data: route, isLoading, isError, error } = useRoute(routeId);
  const [mapsLoading, setMapsLoading] = useState(false);
  const [mapsError, setMapsError] = useState(false);

  // TODO: Loading state and error state do not seem to have a design for this page (these are placeholders for now)
  if (isLoading) {
    return (
      <div className={cn(statusWrapper, className)}>
        <Spinner />
      </div>
    );
  }

  if (isError || !route) {
    return (
      <div className={cn(statusWrapper, 'text-p2 text-grey-500', className)}>
        {isError
          ? `Failed to load route: ${error.message}`
          : 'Route not found.'}
      </div>
    );
  }

  const stops = route.stops ?? [];
  const boxTotal = stops.reduce((sum, stop) => sum + stop.boxes, 0);
  const subtitle = [
    formatDriveDate(route.drive_date),
    formatStartTime(route.start_time),
  ]
    .filter(Boolean)
    .join(' · ');

  const handlePrint = () => window.print();

  const handleGoogleMaps = async () => {
    setMapsError(false);
    setMapsLoading(true);
    // Open the tab synchronously so the user gesture isn't lost to popup
    // blockers while the backend builds the directions URL.
    const tab = window.open('', '_blank');
    try {
      const { data } = await getGoogleMapsLink({
        path: { route_id: routeId },
        throwOnError: true,
      });
      if (tab) {
        tab.opener = null;
        tab.location.href = data;
      } else {
        // Popup was blocked — fall back to navigating the current tab.
        window.location.href = data;
      }
    } catch {
      tab?.close();
      setMapsError(true);
    } finally {
      setMapsLoading(false);
    }
  };

  return (
    <div className={cn('flex flex-col gap-6', className)}>
      {/* Back link */}
      <Link
        to="/driver/home"
        className="text-h2 flex w-fit items-center gap-1 font-bold text-blue-300"
      >
        <ChevronLeft className="size-5" />
        Back to Home
      </Link>

      {/* Header */}
      <div className="flex flex-col gap-1">
        <h1 className="text-h1 text-grey-500 font-bold">
          {route.name || 'Route'}
        </h1>
        {subtitle && <p className="text-p2 text-grey-400">{subtitle}</p>}
      </div>

      {/* Meta: 2-column grid on mobile, single inline row from tablet up. */}
      <div className="text-p2 text-grey-500 [&_svg]:text-grey-400 tablet:flex tablet:flex-wrap tablet:items-center tablet:gap-x-5 grid grid-cols-2 gap-x-4 gap-y-2">
        {route.delivery_type && (
          <span className="flex items-center gap-1.5">
            <Users className="size-4" />
            {route.delivery_type}
          </span>
        )}
        <span className="flex items-center gap-1.5">
          <MapPin className="size-4" />
          {stops.length} {stops.length === 1 ? 'stop' : 'stops'}
        </span>
        <span className="flex items-center gap-1.5">
          <Map className="size-4" />
          {route.length.toFixed(1)} km
        </span>
        <span className="flex items-center gap-1.5">
          <Package className="size-4" />
          {boxTotal} {boxTotal === 1 ? 'box' : 'boxes'}
        </span>
      </div>

      {/* PDF */}
      <Button variant="primary" className="tablet:w-full" onClick={handlePrint}>
        PDF
      </Button>

      {/* Map */}
      <div className="flex flex-col gap-3">
        <h2 className="text-h3 text-grey-500 font-bold">Map View</h2>
        <RouteMap
          encodedPolyline={route.encoded_polyline}
          className="tablet:h-[360px] h-[45vh]"
        />
        <div className="grid grid-cols-2 gap-3">
          <Button asChild variant="secondary" className="tablet:w-full">
            <a href={`tel:${F4K_PHONE}`}>Call Food4Kids</a>
          </Button>
          <Button
            variant="primary"
            className="tablet:w-full"
            onClick={handleGoogleMaps}
            disabled={mapsLoading}
          >
            {mapsLoading ? 'Opening…' : 'Google Maps'}
          </Button>
        </div>
        {mapsError && (
          <p className="text-p2 text-red">
            Couldn&apos;t open Google Maps directions. Please try again.
          </p>
        )}
        <p className="text-p2 text-grey-500">
          If you have any issues with deliveries or reaching families, please
          contact Food4Kids.
        </p>
      </div>

      {/* Stops */}
      <div className="flex flex-col gap-3">
        <h2 className="text-h3 text-grey-500 font-bold">All Stops</h2>
        {stops.length === 0 ? (
          <p className="text-p2 text-grey-500">This route has no stops.</p>
        ) : (
          stops.map((stop) => (
            <RouteStopCard key={stop.stop_number} stop={stop} />
          ))
        )}
      </div>
    </div>
  );
}
