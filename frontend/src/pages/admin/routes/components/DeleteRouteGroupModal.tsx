import type { RouteGroupRead } from '@/api/generated/types.gen';
import { useDeleteRouteGroup } from '@/api/route-groups';
import {
  Button,
  FieldDescription,
  Modal,
  ModalContent,
  ModalDescription,
  ModalHeader,
  ModalTitle,
} from '@/common/components';

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
    <Modal open={open} onOpenChange={handleOpenChange}>
      <ModalContent>
        <ModalHeader>
          <ModalTitle>Delete Route Group</ModalTitle>
          <ModalDescription>
            This will permanently delete route group {routeGroup.name}. This
            action cannot be undone.
          </ModalDescription>
        </ModalHeader>

        <div className="flex items-center justify-end gap-4">
          {isError && (
            <FieldDescription error>
              Something went wrong deleting the group. Please try again.
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
