import { type ReactNode, useState } from 'react';

import { useDrivers } from '@/api/drivers';
import type { RouteDetailRead } from '@/api/generated/types.gen';
import MoreVerticalIcon from '@/assets/icons/more-vertical.svg?react';
import {
  Button,
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/common/components';
import { parseDateOnly } from '@/common/utils';
import { cn } from '@/lib/utils';

import { ReassignDriverModal } from './ReassignDriverModal';

interface RouteOverviewCardProps {
  route: RouteDetailRead;
}

/** "Oct 18, 2025" — the overview card's date format. */
const formatOverviewDate = (isoDate: string): string =>
  parseDateOnly(isoDate).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });

function Metric({ label, children }: { label: string; children: ReactNode }) {
  return (
    // Labels stay top-aligned across columns; the value fills the leftover
    // cell height (grid stretches every cell to the tallest column) and
    // centers its content vertically, so text values line up with the taller
    // control columns (date pill, driver button). 16px (gap-4) label→value.
    <div className="flex flex-col gap-4">
      {/* Label spec (Figma): #1C1B1F (grey-500), 16px (text-p1), bold. */}
      <span className="text-p1 text-grey-500 font-bold">{label}</span>
      {/* Text values render at 18px (text-m-p1); the Assign button overrides
          with its own 16px, per Figma. */}
      <div className="text-m-p1 text-grey-500 flex flex-1 items-center">
        {children}
      </div>
    </div>
  );
}

/** The driver cell: an Assign button when unassigned, else name + kebab. */
function DriverControl({ route }: { route: RouteDetailRead }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const { data: drivers = [] } = useDrivers();

  const driver = drivers.find((d) => d.driver_id === route.driver_id);
  const driverName = driver
    ? `${driver.first_name} ${driver.last_name}`
    : route.driver_id
      ? 'Assigned'
      : null;

  const contextLabel = route.name ? <>{route.name}</> : undefined;

  return (
    <>
      {driverName ? (
        <div className="flex items-center gap-1">
          <span className="text-m-p1 text-grey-500">{driverName}</span>
          <Popover open={menuOpen} onOpenChange={setMenuOpen}>
            <PopoverTrigger asChild>
              <button
                type="button"
                aria-label="Driver actions"
                className="flex size-8 cursor-pointer items-center justify-center rounded-full transition-colors hover:bg-blue-50 data-[state=open]:bg-blue-50"
              >
                <MoreVerticalIcon className="text-grey-400 size-5" />
              </button>
            </PopoverTrigger>
            <PopoverContent
              align="end"
              className="w-auto min-w-0 p-1"
              onOpenAutoFocus={(e) => e.preventDefault()}
            >
              <button
                type="button"
                className="text-p2 text-grey-500 hover:bg-grey-200 flex w-full cursor-pointer items-center rounded-lg px-3 py-2 whitespace-nowrap"
                onClick={() => {
                  setMenuOpen(false);
                  setModalOpen(true);
                }}
              >
                Reassign Driver
              </button>
            </PopoverContent>
          </Popover>
        </div>
      ) : (
        <Button variant="primary" onClick={() => setModalOpen(true)}>
          Assign
        </Button>
      )}

      <ReassignDriverModal
        open={modalOpen}
        onOpenChange={setModalOpen}
        routeId={route.route_id}
        currentDriverName={driverName}
        contextLabel={contextLabel}
      />
    </>
  );
}

/**
 * The Route Overview card: delivery date (editable), delivery type, stop and
 * box counts, distance, and the driver assign/reassign control.
 */
export function RouteOverviewCard({ route }: RouteOverviewCardProps) {
  const stops = route.stops ?? [];
  const boxTotal = stops.reduce((sum, stop) => sum + stop.boxes, 0);

  return (
    <section className="flex flex-col gap-4">
      <h2 className="text-h2 font-nunito-sans text-grey-500 font-bold">
        Route Overview
      </h2>
      <div
        className={cn(
          'border-grey-300 rounded-2xl border bg-white px-6 py-5',
          'tablet:grid-cols-3 desktop:grid-cols-6 grid grid-cols-2 gap-6'
        )}
      >
        <Metric label="Delivery Date">
          {formatOverviewDate(route.drive_date)}
        </Metric>
        <Metric label="Delivery Type">{route.delivery_type ?? '—'}</Metric>
        <Metric label="Stops">{stops.length}</Metric>
        <Metric label="Boxes">{boxTotal}</Metric>
        <Metric label="Distance (km)">{route.length.toFixed(1)}</Metric>
        <Metric label="Driver">
          <DriverControl route={route} />
        </Metric>
      </div>
    </section>
  );
}
