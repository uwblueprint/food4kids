import { useState } from 'react';

import { getRoute } from '@/api/generated/sdk.gen';
import { useRoutes, useUpdateRoute } from '@/api/routes';
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

interface MoveStopModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** The route the stop currently lives on. */
  sourceRouteId: string;
  /** Group whose sibling routes are valid move targets. */
  sourceRouteGroupId: string;
  /** The source route's current stops in order, as location ids. */
  locationIds: string[];
  /** The stop being moved. */
  stopLocationId: string;
  stopAddress: string;
}

/**
 * Moves a stop to a sibling route in the same route group. This is two PATCHes
 * — remove from the source route, then append to the target — each of which
 * re-runs routing for the route it touches.
 */
export function MoveStopModal({
  open,
  onOpenChange,
  sourceRouteId,
  sourceRouteGroupId,
  locationIds,
  stopLocationId,
  stopAddress,
}: MoveStopModalProps) {
  const [targetRouteId, setTargetRouteId] = useState('');
  const [error, setError] = useState(false);
  const [orphaned, setOrphaned] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const { mutateAsync: updateRoute } = useUpdateRoute();

  // Sibling routes share the group; the list endpoint has no group filter, so
  // pull a wide page and narrow to this group (minus the source route).
  const { data } = useRoutes({ page_size: 200 });
  const siblings = (data?.items ?? []).filter(
    (r) =>
      r.route_group_id === sourceRouteGroupId && r.route_id !== sourceRouteId
  );

  const handleOpenChange = (next: boolean) => {
    onOpenChange(next);
    if (!next) {
      setTargetRouteId('');
      setError(false);
      setOrphaned(false);
      setSubmitting(false);
    }
  };

  const handleConfirm = async () => {
    if (!targetRouteId) return;
    setError(false);
    setOrphaned(false);
    setSubmitting(true);
    let removedFromSource = false;
    try {
      // Remove from the source first so the same location never sits on two
      // routes of the group at once (the backend guards against that).
      await updateRoute({
        path: { route_id: sourceRouteId },
        body: {
          location_ids: locationIds.filter((id) => id !== stopLocationId),
        },
      });
      removedFromSource = true;
      // Append to the target, preserving its existing order.
      const { data: target } = await getRoute({
        path: { route_id: targetRouteId },
        throwOnError: true,
      });
      const targetLocationIds = (target.stops ?? []).map((s) => s.location_id);
      await updateRoute({
        path: { route_id: targetRouteId },
        body: { location_ids: [...targetLocationIds, stopLocationId] },
      });
      handleOpenChange(false);
    } catch {
      setError(true);
      setOrphaned(removedFromSource);
      setSubmitting(false);
    }
  };

  return (
    <Modal open={open} onOpenChange={handleOpenChange}>
      <ModalContent>
        <ModalHeader>
          <ModalTitle variant="form">Transfer Stop</ModalTitle>
          <ModalDescription>
            Transfer {stopAddress} to another route in this group. Both routes
            will be re-optimized.
          </ModalDescription>
        </ModalHeader>

        <Field>
          <FieldLabel>Destination route</FieldLabel>
          <Dropdown value={targetRouteId} onValueChange={setTargetRouteId}>
            <DropdownTrigger className="rounded-lg px-3">
              <DropdownValue placeholder="Select a route" />
            </DropdownTrigger>
            <DropdownContent>
              {siblings.map((route) => (
                <DropdownItem key={route.route_id} value={route.route_id}>
                  {route.name ?? 'Route'} — {route.driver_name ?? 'Unassigned'}
                </DropdownItem>
              ))}
            </DropdownContent>
          </Dropdown>
        </Field>

        {siblings.length === 0 && (
          <FieldDescription>
            This group has no other routes to move the stop to.
          </FieldDescription>
        )}
        {error && (
          <FieldDescription error>
            {orphaned
              ? `${stopAddress} was removed from the source route but couldn't be added to the destination. Re-add it with the Add stop button.`
              : 'Something went wrong moving the stop. Please try again.'}
          </FieldDescription>
        )}

        <ModalFooter>
          <Button
            variant="tertiary"
            onClick={() => handleOpenChange(false)}
            disabled={submitting}
          >
            Cancel
          </Button>
          <Button
            variant="primary"
            disabled={!targetRouteId || submitting}
            onClick={handleConfirm}
          >
            Transfer
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}
