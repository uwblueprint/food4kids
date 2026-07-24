import { useDeleteAddress } from '@/api/addresses';
import type { LocationRead } from '@/api/generated/types.gen';
import {
  Button,
  FieldDescription,
  Modal,
  ModalContent,
  ModalDescription,
  ModalHeader,
  ModalTitle,
} from '@/common/components';

interface DeleteAddressModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  address: LocationRead;
}

/** Confirmation dialog for permanently deleting a location/address. */
export function DeleteAddressModal({
  open,
  onOpenChange,
  address,
}: DeleteAddressModalProps) {
  const {
    mutate: deleteAddress,
    isPending,
    isError,
    reset,
  } = useDeleteAddress();

  const handleOpenChange = (next: boolean) => {
    onOpenChange(next);
    if (!next) reset();
  };

  const handleDelete = () => {
    deleteAddress(
      { path: { location_id: address.location_id } },
      { onSuccess: () => handleOpenChange(false) }
    );
  };

  return (
    <Modal open={open} onOpenChange={handleOpenChange}>
      <ModalContent>
        <ModalHeader>
          <ModalTitle>Delete Address</ModalTitle>
          <ModalDescription>
            This will permanently delete {address.contact_name}. This action
            cannot be undone.
          </ModalDescription>
        </ModalHeader>

        <div className="flex items-center justify-end gap-4">
          {isError && (
            <FieldDescription error>
              Something went wrong deleting the address. Please try again.
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
