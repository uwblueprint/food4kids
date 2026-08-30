import { type ReactNode, useState } from 'react';
import { Link } from 'react-router-dom';

import { useDrivers } from '@/api/drivers';
import { useSuggestedDriver, useUpdateRoute } from '@/api/routes';
import {
  Button,
  Dropdown,
  DropdownContent,
  DropdownItem,
  DropdownTrigger,
  DropdownValue,
  Field,
  FieldDescription,
  FieldLabel,
  Modal,
  ModalContent,
  ModalDescription,
  ModalFooter,
  ModalHeader,
  ModalTitle,
  TimePicker,
} from '@/common/components';

/** The design's default start time for a route that has none yet. */
const DEFAULT_START_TIME = '09:00';

/**
 * The API stores start_time as "HH:MM:SS"; TimePicker speaks "HH:MM". Convert
 * at this boundary rather than teaching either side about the other's format.
 */
const toApiTime = (value: string): string => `${value}:00`;
const fromApiTime = (value: string | null | undefined): string =>
  value ? value.slice(0, 5) : DEFAULT_START_TIME;

interface ReassignDriverModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** Route being (re)assigned. */
  routeId: string;
  /** Route group the assignment happens within — scopes the driver suggestion. */
  routeGroupId: string;
  /** Currently assigned driver's name, if any — drives Assign vs Reassign copy. */
  currentDriverName?: string | null;
  /** The route's start time as "HH:MM:SS", if it already has one. */
  startTime?: string | null;
  /** Optional context line under the title, e.g. "Route A • Tuesday • Oct 18". */
  contextLabel?: ReactNode;
  /**
   * Omitted on the individual-route screen, which is already the destination.
   */
  showViewRoute?: boolean;
  /** Called once the (re)assignment saves, e.g. to highlight the row. */
  onUpdated?: () => void;
}

/**
 * The driver (re)assignment dialog shared across the routes admin — the Routes
 * list (the Driver column's "Assign" pill and the kebab's "Reassign Driver")
 * and the individual route screen. Callers pass the primitives it needs so it
 * works from any route shape; reached with a driver already set it reassigns,
 * reached from an unassigned route it assigns.
 *
 * Driver and start time are submitted together because the API rejects an
 * assigned route with no start time (ck_routes_assigned_route_has_start_time),
 * and generated routes start with start_time unset.
 */
export function ReassignDriverModal({
  open,
  onOpenChange,
  routeId,
  routeGroupId,
  currentDriverName,
  startTime,
  contextLabel,
  showViewRoute = true,
  onUpdated,
}: ReassignDriverModalProps) {
  const [driverId, setDriverId] = useState('');
  const [time, setTime] = useState(() => fromApiTime(startTime));
  const { data: drivers = [] } = useDrivers();
  const { data: suggestion } = useSuggestedDriver(routeId, routeGroupId, open);
  const { mutate: updateRoute, isPending, isError, reset } = useUpdateRoute();

  const handleOpenChange = (next: boolean) => {
    onOpenChange(next);
    if (!next) {
      setDriverId('');
      setTime(fromApiTime(startTime));
      reset();
    }
  };

  const handleSubmit = () => {
    if (!driverId) return;
    updateRoute(
      {
        path: { route_id: routeId },
        body: { driver_id: driverId, start_time: toApiTime(time) },
      },
      {
        onSuccess: () => {
          onUpdated?.();
          handleOpenChange(false);
        },
      }
    );
  };

  // Reached from the "Assign" pill there is nobody to reassign from, so it says
  // Assign — the design's own word for that action — and drops the "Currently
  // Assigned: Unassigned" line that only restates it.
  const isReassign = Boolean(currentDriverName);

  return (
    <Modal open={open} onOpenChange={handleOpenChange}>
      <ModalContent>
        <ModalHeader>
          <ModalTitle variant="form">
            {isReassign ? 'Reassign Driver' : 'Assign Driver'}
          </ModalTitle>
          {contextLabel && <ModalDescription>{contextLabel}</ModalDescription>}
        </ModalHeader>

        <div className="flex flex-col gap-4">
          {isReassign && (
            <div className="flex flex-col gap-2">
              <p className="text-p1 text-grey-500 font-semibold">
                Currently Assigned
              </p>
              <p className="border-grey-300 text-p2 text-grey-400 border-l-2 pl-4">
                {currentDriverName}
              </p>
            </div>
          )}

          <Field>
            <FieldLabel required>Driver</FieldLabel>
            <Dropdown value={driverId} onValueChange={setDriverId}>
              <DropdownTrigger className="rounded-lg px-3">
                <DropdownValue placeholder="Select a driver" />
              </DropdownTrigger>
              <DropdownContent>
                {drivers.map((driver) => (
                  <DropdownItem key={driver.driver_id} value={driver.driver_id}>
                    {driver.first_name} {driver.last_name}
                  </DropdownItem>
                ))}
              </DropdownContent>
            </Dropdown>
            {/* Absent when nobody has driven these stops before, or when every
                candidate is already booked elsewhere in the group. */}
            {suggestion && (
              <FieldDescription>
                Similar routes driven by {suggestion.driver_name}
              </FieldDescription>
            )}
          </Field>

          <Field>
            <FieldLabel required>Start Time</FieldLabel>
            <TimePicker
              value={time}
              onChange={setTime}
              className="w-full rounded-xl"
            />
          </Field>
        </div>

        {isError && (
          <FieldDescription error>
            Something went wrong {isReassign ? 'reassigning' : 'assigning'} the
            driver. Please try again.
          </FieldDescription>
        )}
        <ModalFooter>
          <Button
            variant="tertiary"
            onClick={() => handleOpenChange(false)}
            disabled={isPending}
          >
            Cancel
          </Button>
          <div className="flex items-center gap-2.5">
            {showViewRoute && (
              <Button variant="secondary" asChild>
                <Link to={`/admin/routes/${routeId}`}>View route</Link>
              </Button>
            )}
            <Button
              variant="primary"
              disabled={!driverId || isPending}
              onClick={handleSubmit}
            >
              {isReassign ? 'Reassign' : 'Assign'}
            </Button>
          </div>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}
