import { useQueryClient } from '@tanstack/react-query';
import { ChevronDown } from 'lucide-react';
import { type ReactNode, useState } from 'react';

import { useDrivers } from '@/api/drivers';
import { getRouteQueryKey } from '@/api/generated/@tanstack/react-query.gen';
import type { RouteDetailRead } from '@/api/generated/types.gen';
import { useUpdateRouteGroup } from '@/api/route-groups';
import MoreVerticalIcon from '@/assets/icons/more-vertical.svg?react';
import {
  Button,
  Calendar,
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/common/components';
import { parseDateOnly, toNaiveDateString } from '@/common/utils';
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
      {/* Text values render at 18px (text-m-p1); the Date pill and Assign
          button override with their own 16px, per Figma. */}
      <div className="text-m-p1 text-grey-500 flex flex-1 items-center">
        {children}
      </div>
    </div>
  );
}

/** Inline delivery-date editor: a bordered control that opens a calendar. */
function DeliveryDateEditor({
  routeId,
  routeGroupId,
  driveDate,
}: {
  routeId: string;
  routeGroupId: string;
  driveDate: string;
}) {
  const [open, setOpen] = useState(false);
  const queryClient = useQueryClient();
  const { mutate: updateRouteGroup } = useUpdateRouteGroup();

  const selected = parseDateOnly(driveDate);
  const [, timePart = '00:00:00'] = driveDate.split('T');

  const handleSelect = (date: Date | undefined) => {
    if (!date) return;
    updateRouteGroup(
      {
        path: { route_group_id: routeGroupId },
        body: { drive_date: `${toNaiveDateString(date)}T${timePart}` },
      },
      {
        // The group hook refreshes the route lists, but this page reads the
        // route detail (GET /routes/{id}), which drive_date also feeds — so
        // invalidate it here or the card keeps showing the old date.
        onSuccess: () =>
          queryClient.invalidateQueries({
            queryKey: getRouteQueryKey({ path: { route_id: routeId } }),
          }),
      }
    );
    setOpen(false);
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        {/* Pill trigger mirroring the shared Dropdown (rounded-full). */}
        <button
          type="button"
          className={cn(
            'inline-flex cursor-pointer items-center justify-between gap-2 rounded-full px-6 py-3',
            'text-p1 text-grey-500 transition-colors',
            'bg-grey-100 outline-grey-300 outline outline-1 outline-offset-[-1px]',
            'focus:outline-2 focus:outline-blue-300',
            'data-[state=open]:outline-2 data-[state=open]:outline-blue-300'
          )}
        >
          {formatOverviewDate(driveDate)}
          <ChevronDown className="text-grey-500 size-4 shrink-0" />
        </button>
      </PopoverTrigger>
      <PopoverContent
        align="start"
        className="w-auto p-0"
        onOpenAutoFocus={(e) => e.preventDefault()}
      >
        <Calendar
          mode="single"
          selected={selected}
          onSelect={handleSelect}
          defaultMonth={selected}
          classNames={{
            month_caption: 'flex h-(--cell-size) items-center pl-1',
            nav: 'absolute top-0 right-0 flex items-center gap-1',
          }}
        />
      </PopoverContent>
    </Popover>
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
          <span className="text-p1 text-grey-500">{driverName}</span>
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
                Reassign driver
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
        routeGroupId={route.route_group_id}
        currentDriverName={driverName}
        startTime={route.start_time}
        contextLabel={contextLabel}
        showViewRoute={false}
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
          <DeliveryDateEditor
            routeId={route.route_id}
            routeGroupId={route.route_group_id}
            driveDate={route.drive_date}
          />
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
