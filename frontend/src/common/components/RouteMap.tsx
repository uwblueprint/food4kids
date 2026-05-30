import 'leaflet/dist/leaflet.css';

import polyline from '@mapbox/polyline';
import { useEffect, useMemo } from 'react';
import { MapContainer, Polyline, TileLayer, useMap } from 'react-leaflet';

import { cn } from '@/lib/utils';

// Waterloo, ON — fallback when no polyline is available.
const DEFAULT_CENTER: [number, number] = [43.4643, -80.5204];
const DEFAULT_ZOOM = 12;
const POLYLINE_COLOR = '#226ca7'; // --color-blue-300
const POLYLINE_CASING_COLOR = '#ffffff'; // --color-grey-100

export interface RouteMapProps {
  /** Google-encoded polyline string (precision 5, [lat, lng] order). */
  encodedPolyline: string | null;
  className?: string;
}

/** Fits the map to the polyline bounds on mount / when coords change. */
function FitToPolyline({ coords }: { coords: [number, number][] }) {
  const map = useMap();
  useEffect(() => {
    if (coords.length > 0) {
      map.fitBounds(coords, { padding: [24, 24] });
    }
  }, [coords, map]);
  return null;
}

export function RouteMap({ encodedPolyline, className }: RouteMapProps) {
  const coords = useMemo<[number, number][]>(() => {
    if (!encodedPolyline) return [];
    return polyline.decode(encodedPolyline);
  }, [encodedPolyline]);

  const center = coords[0] ?? DEFAULT_CENTER;

  return (
    <div
      className={cn(
        'w-full overflow-hidden rounded-2xl border border-grey-300',
        className
      )}
    >
      <MapContainer
        center={center}
        zoom={DEFAULT_ZOOM}
        scrollWheelZoom
        className="h-full w-full"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {coords.length > 0 && (
          <>
            {/* White casing underneath for contrast against busy tiles */}
            <Polyline
              positions={coords}
              pathOptions={{ color: POLYLINE_CASING_COLOR, weight: 9, opacity: 0.9 }}
            />
            {/* Main route line on top */}
            <Polyline
              positions={coords}
              pathOptions={{ color: POLYLINE_COLOR, weight: 5, opacity: 1 }}
            />
            <FitToPolyline coords={coords} />
          </>
        )}
      </MapContainer>
    </div>
  );
}