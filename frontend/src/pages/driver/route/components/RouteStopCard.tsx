import { useState } from 'react';

import { ChevronDown } from 'lucide-react';

import type { RouteStopDetailRead } from '@/api/generated/types.gen';

import { DotSeparated } from './DotSeparated';
import { StopContactSection } from './StopContactSection';
import { StopNotesSection } from './StopNotesSection';

export interface RouteStopCardProps {
  stop: RouteStopDetailRead;
}

/** Split a Google-formatted address ("Unit 5, 123 Main St, Waterloo, ON N2L
 *  3G1, Canada") into the street line and the city.
 *
 *  Counted from the END, because that is the stable part of the format —
 *  country last, then region + postal code, then the city. The street is
 *  whatever precedes those, and it is *not* always one segment: a unit or
 *  suite number gets its own. Reading parts[0]/parts[1] instead puts "Unit 5"
 *  on the street line and the street itself on the city line.
 *
 *  An address without those trailing segments is shown whole rather than
 *  guessed at — a long street line is better than a confidently wrong one on
 *  a card a driver navigates by. */
function splitAddress(address: string): {
  street: string;
  city: string | null;
} {
  const parts = address
    .split(',')
    .map((part) => part.trim())
    .filter(Boolean);
  // <street…>, <city>, <region postal>, <country>
  if (parts.length < 4) return { street: address, city: null };
  return {
    street: parts.slice(0, -3).join(', '),
    city: parts.at(-3) ?? null,
  };
}

/** A single delivery stop: collapsed shows address + boxes; expanding reveals
 *  notes and contact. */
export function RouteStopCard({ stop }: RouteStopCardProps) {
  const [expanded, setExpanded] = useState(false);
  const { street, city } = splitAddress(stop.address);
  const boxLabel = `${stop.boxes} ${stop.boxes === 1 ? 'box' : 'boxes'}`;
  const subLine = [city, boxLabel].filter(Boolean);

  return (
    <details
      className="group border-grey-300 rounded-xl border bg-white p-3"
      onToggle={(event) => {
        setExpanded(event.currentTarget.open);
      }}
    >
      <summary className="flex cursor-pointer list-none items-start gap-4 [&::-webkit-details-marker]:hidden">
        {/* Stop number badge */}
        <span className="bg-grey-200 text-button font-nunito text-grey-500 flex size-7 shrink-0 items-center justify-center rounded-full font-semibold">
          {stop.stop_number}
        </span>

        <div className="flex min-w-0 flex-1 flex-col">
          <p className="text-p1 text-grey-500 break-words">{street}</p>
          <DotSeparated
            items={subLine}
            className="text-p2 tablet:font-semibold text-grey-500"
          />
        </div>

        <ChevronDown className="text-grey-500 size-6 shrink-0 transition-transform group-open:rotate-180" />
      </summary>

      {expanded && (
        <div className="bg-grey-200 -mx-3 mt-3 -mb-3 flex flex-col gap-6 rounded-b-xl px-3 py-5">
          <StopNotesSection
            noteChainId={stop.note_chain_id}
            enabled={expanded}
          />
          <StopContactSection stop={stop} />
        </div>
      )}
    </details>
  );
}
