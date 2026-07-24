import { ChevronDown } from 'lucide-react';

import type { RouteStopDetailRead } from '@/api/generated/types.gen';

export interface RouteStopCardProps {
  stop: RouteStopDetailRead;
}

/** Split a combined address ("123 Main St, Waterloo, ON N2L 3G1, Canada") into
 *  the street line and the city. Falls back to the whole string as the street
 *  when there are no comma-separated segments to work with. */
function splitAddress(address: string): {
  street: string;
  city: string | null;
} {
  const parts = address
    .split(',')
    .map((part) => part.trim())
    .filter(Boolean);
  return {
    street: parts[0] ?? address,
    city: parts.length > 1 ? parts[1] : null,
  };
}

/** A single delivery stop: collapsed shows address + boxes; expanding reveals
 *  contact/phone and (eventually) notes. */
export function RouteStopCard({ stop }: RouteStopCardProps) {
  const { street, city } = splitAddress(stop.address);
  const boxLabel = `${stop.boxes} ${stop.boxes === 1 ? 'box' : 'boxes'}`;
  const subLine = [city, boxLabel].filter(Boolean).join(' · ');

  return (
    <details className="group border-grey-300 rounded-xl border bg-white p-4">
      <summary className="flex cursor-pointer list-none items-start gap-3 [&::-webkit-details-marker]:hidden">
        {/* Stop number badge */}
        <span className="bg-grey-200 text-p2 text-grey-500 flex size-7 shrink-0 items-center justify-center rounded-full font-bold">
          {stop.stop_number}
        </span>

        <div className="flex min-w-0 flex-1 flex-col gap-0.5">
          <p className="text-p1 text-grey-500 font-semibold break-words">
            {street}
          </p>
          <p className="text-p2 text-grey-400">{subLine}</p>
        </div>

        <ChevronDown className="text-grey-400 size-5 shrink-0 transition-transform group-open:rotate-180" />
      </summary>

      {/* Expanded content */}
      <div className="border-grey-300 mt-3 border-t pt-3">
        {/* TODO: Add Notes Rendering */}
        <p className="text-p2 text-grey-400">TODO: Add Notes Rendering</p>
      </div>
    </details>
  );
}
