import { useDeleteAddress } from '@/api/addresses';
import type { LocationRead } from '@/api/generated/types.gen';

import { ConfirmDeleteModal } from './ConfirmDeleteModal';

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
    <ConfirmDeleteModal
      open={open}
      onOpenChange={handleOpenChange}
      title="Delete Address"
      description={
        <>
          This will permanently delete {address.contact_name}. This action
          cannot be undone.
        </>
      }
      isPending={isPending}
      isError={isError}
      errorMessage="Something went wrong deleting the address. Please try again."
      onConfirm={handleDelete}
    />
  );
}
