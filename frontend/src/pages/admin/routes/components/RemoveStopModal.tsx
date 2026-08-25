import { useUpdateRoute } from '@/api/routes';

import { ConfirmDeleteModal } from './ConfirmDeleteModal';

interface RemoveStopModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  routeId: string;
  /** Route name shown in the confirmation copy. */
  routeName: string;
  /** The route's current stops in order, as location ids. */
  locationIds: string[];
  /** The stop being removed. */
  stopLocationId: string;
  /** Address shown in the confirmation copy. */
  stopAddress: string;
}

/**
 * Confirmation dialog for removing a stop. Rebuilds the route's ordered
 * location list without this stop and PATCHes it, which re-runs routing.
 */
export function RemoveStopModal({
  open,
  onOpenChange,
  routeId,
  routeName,
  locationIds,
  stopLocationId,
  stopAddress,
}: RemoveStopModalProps) {
  const { mutate: updateRoute, isPending, isError, reset } = useUpdateRoute();

  const handleOpenChange = (next: boolean) => {
    onOpenChange(next);
    if (!next) reset();
  };

  const handleConfirm = () => {
    updateRoute(
      {
        path: { route_id: routeId },
        body: {
          location_ids: locationIds.filter((id) => id !== stopLocationId),
        },
      },
      { onSuccess: () => handleOpenChange(false) }
    );
  };

  return (
    <ConfirmDeleteModal
      open={open}
      onOpenChange={handleOpenChange}
      title="Delete Stop"
      description={
        <span className="text-grey-500">
          This will delete the{' '}
          <strong className="font-bold">{stopAddress}</strong> stop from{' '}
          <strong className="font-bold">{routeName}</strong>. You can add it
          again later with the Add Stop button.
        </span>
      }
      isPending={isPending}
      isError={isError}
      errorMessage="Something went wrong removing the stop. Please try again."
      onConfirm={handleConfirm}
    />
  );
}
