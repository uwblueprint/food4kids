import 'leaflet/dist/leaflet.css';

import polyline from '@mapbox/polyline';
import L from 'leaflet';
import { useEffect, useMemo } from 'react';
import {
  MapContainer,
  Marker,
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
// Stop markers: a blue-400 disc in a white ring carrying the stop number,
// sized to the numbered badge in the route's StopsTable. A divIcon rather
// than a CircleMarker because an SVG circle cannot hold a label.
const STOP_DIAMETER = 21;
const STOP_RING_WEIGHT = 3;
const STOP_RING_COLOR = '#ffffff'; // --color-grey-100
const MUTED_COLOR = '#A8A8A8';

function stopIcon(stopNumber: number, muted?: boolean) {
  const fill = muted ? MUTED_COLOR : POLYLINE_COLOR;
  return L.divIcon({
    // Leaflet's default .leaflet-div-icon paints a white box with a border;
    // blanking the class leaves only the disc below.
    className: '',
    html: `<span style="display:flex;align-items:center;justify-content:center;box-sizing:border-box;width:${STOP_DIAMETER}px;height:${STOP_DIAMETER}px;border-radius:9999px;background:${fill};border:${STOP_RING_WEIGHT}px solid ${STOP_RING_COLOR};color:#fff;font-size:11px;font-weight:700;line-height:1">${stopNumber}</span>`,
    iconSize: [STOP_DIAMETER, STOP_DIAMETER],
    // Centre the disc on the coordinate; the default anchors it by its top-left.
    iconAnchor: [STOP_DIAMETER / 2, STOP_DIAMETER / 2],
  });
}

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
  /** When true, render the polyline and stops in a muted/grey style. */
  muted?: boolean;
  /** Choose the basemap tileset. 'default' = color OSM, 'grey' = desaturated basemap. */
  basemap?: 'default' | 'grey';
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

/** Fits the map to the stop bounds when there are no polyline coordinates. */
function FitToStops({ stopPositions }: { stopPositions: [number, number][] }) {
  const map = useMap();
  useEffect(() => {
    if (stopPositions.length > 0) {
      map.fitBounds(stopPositions, { padding: [24, 24] });
    }
  }, [stopPositions, map]);
  return null;
}

export function RouteMap({
  encodedPolyline,
  stops,
  className,
  muted,
  basemap = 'default',
}: RouteMapProps) {
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
                icon: stopIcon(stop.stop_number, muted),
              },
            ]
      ),
    [stops, muted]
  );

  const stopPositions = useMemo(
    () => stopPoints.map((p) => p.position),
    [stopPoints]
  );

  const center = coords[0] ?? stopPositions[0] ?? DEFAULT_CENTER;

  return (
    <div
      className={cn(
        // 18px: the only radius in the designs that is off the 8/16 scale.
        // `isolate` gives the map its own stacking context so Leaflet's
        // internal z-indexes (panes/controls up to ~1000) stay contained and
        // can't paint over root-level modals/menus (which sit at z-50).
        'border-grey-300 isolate w-full overflow-hidden rounded-[18px] border',
        className
      )}
    >
      <MapContainer
        center={center}
        zoom={DEFAULT_ZOOM}
        scrollWheelZoom
        className="h-full w-full"
        style={
          basemap === 'grey'
            ? { filter: 'grayscale(100%) brightness(0.9)' }
            : undefined
        }
      >
        {/* Choose a basemap: default OSM color or a greyscale tileset for muted previews */}
        <TileLayer
          attribution={
            basemap === 'grey'
              ? '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; CARTO'
              : '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          }
          url={
            basemap === 'grey'
              ? 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png'
              : 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
          }
          subdomains={
            basemap === 'grey' ? ['a', 'b', 'c', 'd'] : ['a', 'b', 'c']
          }
        />
        {coords.length > 0 && (
          <>
            <Polyline
              positions={coords}
              pathOptions={{
                color: muted ? MUTED_COLOR : POLYLINE_COLOR,
                weight: POLYLINE_WEIGHT,
                opacity: 1,
                lineCap: 'round',
                lineJoin: 'round',
              }}
            />
            <FitToPolyline coords={coords} />
          </>
        )}
        {coords.length === 0 && stopPositions.length > 0 && (
          <FitToStops stopPositions={stopPositions} />
        )}
        {stopPoints.map(({ key, position, icon }) => (
          <Marker
            key={key}
            position={position}
            icon={icon}
            alt={`Stop ${key}`}
          />
        ))}
      </MapContainer>
    </div>
  );
}
