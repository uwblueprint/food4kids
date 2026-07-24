import type { RouteGroupRead } from '@/api/generated/types.gen';
import { useDeleteRouteGroup } from '@/api/route-groups';

import { ConfirmDeleteModal } from './ConfirmDeleteModal';

interface DeleteRouteGroupModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  routeGroup: RouteGroupRead;
}

/** Confirmation dialog for permanently deleting a route group. */
export function DeleteRouteGroupModal({
  open,
  onOpenChange,
  routeGroup,
}: DeleteRouteGroupModalProps) {
  const {
    mutate: deleteRouteGroup,
    isPending,
    isError,
    reset,
  } = useDeleteRouteGroup();

  const handleOpenChange = (next: boolean) => {
    onOpenChange(next);
    if (!next) reset();
  };

  const handleDelete = () => {
    deleteRouteGroup(
      { path: { route_group_id: routeGroup.route_group_id } },
      { onSuccess: () => handleOpenChange(false) }
    );
  };

  return (
    <ConfirmDeleteModal
      open={open}
      onOpenChange={handleOpenChange}
      title="Delete Route Group"
      description={
        <>
          This will permanently delete route group {routeGroup.name}. This
          action cannot be undone.
        </>
      }
      isPending={isPending}
      isError={isError}
      errorMessage="Something went wrong deleting the group. Please try again."
      onConfirm={handleDelete}
    />
  );
}
