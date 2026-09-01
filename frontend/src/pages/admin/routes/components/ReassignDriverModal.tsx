import { type ReactNode, useState } from 'react';

import { useDrivers } from '@/api/drivers';
import { useUpdateRoute } from '@/api/routes';
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
} from '@/common/components';

interface ReassignDriverModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** Route being (re)assigned. */
  routeId: string;
  /** Currently assigned driver's name, if any — drives Assign vs Reassign copy. */
  currentDriverName?: string | null;
  /** Optional context line under the title, e.g. "Route A • Tuesday • Oct 18". */
  contextLabel?: ReactNode;
  /** Called once the (re)assignment saves, e.g. to highlight the row. */
  onUpdated?: () => void;
}

/**
 * The driver (re)assignment dialog shared across the routes admin — the Routes
 * list (the Driver column's "Assign" pill and the kebab's "Reassign Driver")
 * and the individual route screen. Callers pass the primitives it needs so it
 * works from any route shape; reached with a driver already set it reassigns,
 * reached from an unassigned route it assigns.
 */
export function ReassignDriverModal({
  open,
  onOpenChange,
  routeId,
  currentDriverName,
  contextLabel,
  onUpdated,
}: ReassignDriverModalProps) {
  const [driverId, setDriverId] = useState('');
  const { data: drivers = [] } = useDrivers();
  const { mutate: updateRoute, isPending, isError, reset } = useUpdateRoute();

  const handleOpenChange = (next: boolean) => {
    onOpenChange(next);
    if (!next) {
      setDriverId('');
      reset();
    }
  };

  const handleSubmit = () => {
    if (!driverId) return;
    updateRoute(
      {
        path: { route_id: routeId },
        body: { driver_id: driverId },
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
            <FieldLabel>New Driver</FieldLabel>
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
          <Button
            variant="primary"
            disabled={!driverId || isPending}
            onClick={handleSubmit}
          >
            {isReassign ? 'Reassign' : 'Assign'}
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}
