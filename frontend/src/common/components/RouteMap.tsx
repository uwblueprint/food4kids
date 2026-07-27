import 'leaflet/dist/leaflet.css';

import polyline from '@mapbox/polyline';
import { useEffect, useMemo } from 'react';
import {
  CircleMarker,
  MapContainer,
  Polyline,
  TileLayer,
  useMap,
} from 'react-leaflet';

import { cn } from '@/lib/utils';

// Waterloo, ON — fallback when no polyline is available.
const DEFAULT_CENTER: [number, number] = [43.4643, -80.5204];
const DEFAULT_ZOOM = 12;
// Per the route frames: a single blue-400 stroke, 5px, rounded joins and
// caps. No white casing — the frames draw the line bare over the map.
const POLYLINE_COLOR = '#195586'; // --color-blue-400
const POLYLINE_WEIGHT = 5;
/*
 * Stop dots: a 14px blue-400 disc inside a 5px white ring, per the frames.
 * Leaflet centres a stroke on the path, so the radius is the 7px disc plus
 * half the ring — that puts the white between 7px and 12px out, and the fill
 * shows through as a 7px disc underneath it.
 */
const STOP_RADIUS = 9.5;
const STOP_RING_WEIGHT = 5;
const STOP_RING_COLOR = '#ffffff'; // --color-grey-100

/** A stop to mark on the line. Coordinates are nullable upstream — a location
 *  that has not been geocoded yet simply isn't drawn. */
export interface RouteMapStop {
  stop_number: number;
  latitude?: number | null;
  longitude?: number | null;
}

export interface RouteMapProps {
  /** Google-encoded polyline string (precision 5, [lat, lng] order). */
  encodedPolyline: string | null | undefined;
  stops?: RouteMapStop[];
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

export function RouteMap({ encodedPolyline, stops, className }: RouteMapProps) {
  const coords = useMemo<[number, number][]>(() => {
    if (!encodedPolyline) return [];
    try {
      return polyline.decode(encodedPolyline);
    } catch {
      return [];
    }
  }, [encodedPolyline]);

  const stopPoints = useMemo(
    () =>
      (stops ?? []).flatMap((stop) =>
        stop.latitude == null || stop.longitude == null
          ? []
          : [
              {
                key: stop.stop_number,
                position: [stop.latitude, stop.longitude] as [number, number],
              },
            ]
      ),
    [stops]
  );

  const center = coords[0] ?? stopPoints[0]?.position ?? DEFAULT_CENTER;

  return (
    <div
      className={cn(
        'border-grey-300 w-full overflow-hidden rounded-2xl border',
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
            <Polyline
              positions={coords}
              pathOptions={{
                color: POLYLINE_COLOR,
                weight: POLYLINE_WEIGHT,
                opacity: 1,
                lineCap: 'round',
                lineJoin: 'round',
              }}
            />
            <FitToPolyline coords={coords} />
          </>
        )}
        {stopPoints.map(({ key, position }) => (
          <CircleMarker
            key={key}
            center={position}
            radius={STOP_RADIUS}
            pathOptions={{
              color: STOP_RING_COLOR,
              weight: STOP_RING_WEIGHT,
              fillColor: POLYLINE_COLOR,
              fillOpacity: 1,
              opacity: 1,
            }}
          />
        ))}
      </MapContainer>
    </div>
  );
}
