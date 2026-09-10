import type { RouteWithDateRead } from '@/api/generated/types.gen';
import { useDeleteRoute } from '@/api/routes';
import { ConfirmModal } from '@/common/components';

interface DeleteRouteModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  route: RouteWithDateRead;
}

/** Confirmation dialog for permanently deleting a route. */
export function DeleteRouteModal({
  open,
  onOpenChange,
  route,
}: DeleteRouteModalProps) {
  const { mutate: deleteRoute, isPending, isError, reset } = useDeleteRoute();

  const handleOpenChange = (next: boolean) => {
    onOpenChange(next);
    if (!next) reset();
  };

  const handleDelete = () => {
    deleteRoute(
      { path: { route_id: route.route_id } },
      { onSuccess: () => handleOpenChange(false) }
    );
  };

  return (
    <ConfirmModal
      open={open}
      onOpenChange={handleOpenChange}
      title="Delete Route"
      description={
        <>
          This will permanently delete route {route.name}. This action cannot be
          undone.
        </>
      }
      confirmLabel="Delete"
      confirmVariant="destructive"
      isLoading={isPending}
      error={
        isError
          ? 'Something went wrong deleting the route. Please try again.'
          : null
      }
      onConfirm={handleDelete}
    />
  );
}
