import { useState } from 'react';

import { useDrivers } from '@/api/drivers';
import type { RouteWithDateRead } from '@/api/generated/types.gen';
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
import { parseDateOnly } from '@/common/utils';

interface ReassignDriverModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  route: RouteWithDateRead;
  /** Called once the reassignment saves, e.g. to highlight the row. */
  onUpdated?: () => void;
}

/** "Oct 18" — short date for the dialog's context line. */
const formatContextDate = (isoDate: string): string =>
  parseDateOnly(isoDate).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  });

export function ReassignDriverModal({
  open,
  onOpenChange,
  route,
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
        path: { route_id: route.route_id },
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

  return (
    <Modal open={open} onOpenChange={handleOpenChange}>
      <ModalContent>
        <ModalHeader>
          <ModalTitle>Reassign Driver</ModalTitle>
          <ModalDescription>
            {route.name} • {route.group_name} •{' '}
            {formatContextDate(route.drive_date)}
          </ModalDescription>
        </ModalHeader>

        <div className="flex flex-col gap-4">
          <div className="flex flex-col gap-2">
            <p className="text-p1 text-grey-500 font-semibold">
              Currently Assigned
            </p>
            <p className="border-grey-300 text-p2 text-grey-400 border-l-2 pl-4">
              {route.driver_name ?? 'Unassigned'}
            </p>
          </div>

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
            Something went wrong reassigning the driver. Please try again.
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
            Reassign
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}
