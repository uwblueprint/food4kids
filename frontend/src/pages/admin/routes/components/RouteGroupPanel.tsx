import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';

import { useDrivers } from '@/api/drivers';
import type {
  RouteGroupRead,
  RouteWithDateRead,
} from '@/api/generated/types.gen';
import { useRoutes, useUpdateRoute } from '@/api/routes';
import ExternalLinkIcon from '@/assets/icons/external-link.svg?react';
import ClosePanelIcon from '@/assets/icons/right-panel-close.svg?react';
import {
  Dropdown,
  DropdownContent,
  DropdownItem,
  DropdownTrigger,
  DropdownValue,
} from '@/common/components';
import { orDash, parseDateOnly } from '@/common/utils';

import { DEFAULT_START_TIME } from './ReassignDriverModal';

/** Route number badges cycle through the brand palette, per the design. */
const BADGE_COLORS = [
  'bg-brand-light-blue',
  'bg-brand-orange',
  'bg-brand-pink',
  'bg-brand-green',
] as const;

// Radix Select reserves '' for "no value", so unassigned needs its own value.
const UNASSIGNED = 'unassigned';

/** "Tuesday, Oct 14" */
const formatHeaderDate = (isoDate: string): string =>
  parseDateOnly(isoDate).toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'short',
    day: 'numeric',
  });

/** "Oct 1, 2025 at 11:48 AM" */
const formatCreatedAt = (value: string): string => {
  const date = new Date(value);
  const day = date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
  const time = date.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
  });
  return `${day} at ${time}`;
};

function Stat({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
      <dt className="text-p1 text-grey-500 font-bold">{label}</dt>
      <dd className="text-m-p1 text-grey-500">{children}</dd>
    </div>
  );
}

/**
 * Assigns a driver straight from the panel. The API rejects an assigned route
 * with no start time, so a route that has none gets the same default the
 * assign dialog offers.
 */
function RouteDriverSelect({ route }: { route: RouteWithDateRead }) {
  const { data: drivers = [] } = useDrivers();
  const { mutate: updateRoute, isPending, isError } = useUpdateRoute();

  // The current driver may fall outside the fetched list (e.g. inactive), and
  // Radix renders a blank trigger for a value with no matching item.
  const currentMissing =
    route.driver_id && !drivers.some((d) => d.driver_id === route.driver_id);

  const handleChange = (value: string) => {
    const driverId = value === UNASSIGNED ? null : value;
    if (driverId === (route.driver_id ?? null)) return;
    updateRoute({
      path: { route_id: route.route_id },
      body: driverId
        ? {
            driver_id: driverId,
            start_time: route.start_time ?? `${DEFAULT_START_TIME}:00`,
          }
        : { driver_id: null },
    });
  };

  return (
    <div className="flex flex-col items-end gap-1">
      <Dropdown
        value={route.driver_id ?? UNASSIGNED}
        onValueChange={handleChange}
        disabled={isPending}
      >
        <DropdownTrigger
          aria-label={`Driver for ${route.name}`}
          className="text-p3 w-44 py-1.5 [&>span]:truncate"
        >
          <DropdownValue />
        </DropdownTrigger>
        <DropdownContent>
          <DropdownItem value={UNASSIGNED}>No Driver Assigned</DropdownItem>
          {currentMissing && route.driver_id && (
            <DropdownItem value={route.driver_id}>
              {route.driver_name}
            </DropdownItem>
          )}
          {drivers.map((driver) => (
            <DropdownItem key={driver.driver_id} value={driver.driver_id}>
              {driver.first_name} {driver.last_name}
            </DropdownItem>
          ))}
        </DropdownContent>
      </Dropdown>
      {isError && (
        <span className="text-p3 text-red">Couldn&apos;t update driver</span>
      )}
    </div>
  );
}

interface RouteGroupPanelProps {
  group: RouteGroupRead;
  onClose: () => void;
}

export function RouteGroupPanel({ group, onClose }: RouteGroupPanelProps) {
  const { data, isLoading } = useRoutes({
    route_group_id: group.route_group_id,
    page_size: 200,
  });
  const routes = data?.items ?? [];

  return (
    <aside className="border-grey-300 bg-grey-200 shadow-harsh fixed top-0 right-0 z-40 h-screen w-[430px] overflow-y-auto border-l">
      <div className="flex flex-col gap-4 p-6">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-h1 text-grey-500 font-bold">{group.name}</h2>
            <p className="text-p1 text-grey-400 mt-1">
              {formatHeaderDate(group.drive_date)}
            </p>
          </div>
          <button
            type="button"
            aria-label="Close route group panel"
            onClick={onClose}
            className="border-grey-300 flex size-9 items-center justify-center rounded-full border bg-white text-blue-300"
          >
            <ClosePanelIcon className="size-4" />
          </button>
        </div>

        <section className="rounded-2xl bg-white p-5">
          <h3 className="text-h2 text-grey-500 mb-4 font-bold">
            Group Overview
          </h3>
          <dl className="grid grid-cols-3 gap-x-4 gap-y-4">
            <Stat label="Delivery Type">{orDash(group.delivery_type)}</Stat>
            <Stat label="Routes">{orDash(group.num_routes)}</Stat>
            <Stat label="Locations">{orDash(group.num_locations)}</Stat>
            <Stat label="Boxes">{orDash(group.num_boxes)}</Stat>
            <Stat label="Drivers">{orDash(group.num_drivers_assigned)}</Stat>
            <Stat label="Status">{group.status}</Stat>
          </dl>
        </section>

        <section className="rounded-2xl bg-white p-5">
          <h3 className="text-h2 text-grey-500 mb-3 font-bold">
            Routes in this Group
          </h3>
          <div className="text-grey-400 flex justify-between pb-2 text-[13px]">
            <span>Route Name</span>
            <span className="w-44">Driver Name</span>
          </div>
          {isLoading ? null : routes.length ? (
            <ul className="divide-grey-200 flex flex-col divide-y">
              {routes.map((route, index) => (
                <li
                  key={route.route_id}
                  className="flex items-center justify-between gap-3 py-3"
                >
                  <div className="flex min-w-0 items-center gap-3">
                    <span
                      className={`flex size-6 shrink-0 items-center justify-center rounded-full text-xs font-bold text-white ${BADGE_COLORS[index % BADGE_COLORS.length]}`}
                    >
                      {index + 1}
                    </span>
                    <div className="min-w-0">
                      <Link
                        to={`/admin/routes/${route.route_id}`}
                        className="text-p1 flex items-center gap-1 font-semibold text-blue-300 hover:underline"
                      >
                        <span className="truncate">{route.name}</span>
                        <ExternalLinkIcon className="size-3.5 shrink-0" />
                      </Link>
                      <p className="text-p2 text-grey-400">
                        {route.num_stops} Stops · {route.box_total} Boxes
                      </p>
                    </div>
                  </div>
                  <RouteDriverSelect route={route} />
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-p3 text-grey-400 py-3 text-center">
              No routes generated yet
            </p>
          )}
        </section>

        {group.created_at && (
          <p className="text-p1 text-grey-400 text-center">
            Group created on {formatCreatedAt(group.created_at)}
          </p>
        )}
      </div>
    </aside>
  );
}
