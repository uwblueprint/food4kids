import type { RouteWithDateRead } from '@/api/generated/types.gen';
import { useDeleteRoute } from '@/api/routes';
import {
  Button,
  FieldDescription,
  Modal,
  ModalContent,
  ModalDescription,
  ModalHeader,
  ModalTitle,
} from '@/common/components';

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
    <Modal open={open} onOpenChange={handleOpenChange}>
      <ModalContent>
        <ModalHeader>
          <ModalTitle>Delete Route</ModalTitle>
          <ModalDescription>
            This will permanently delete route {route.name}. This action cannot
            be undone.
          </ModalDescription>
        </ModalHeader>

        <div className="flex items-center justify-end gap-4">
          {isError && (
            <FieldDescription error>
              Something went wrong deleting the route. Please try again.
            </FieldDescription>
          )}
          <Button
            variant="tertiary"
            onClick={() => handleOpenChange(false)}
            disabled={isPending}
          >
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={handleDelete}
            disabled={isPending}
          >
            Delete
          </Button>
        </div>
      </ModalContent>
    </Modal>
  );
}
