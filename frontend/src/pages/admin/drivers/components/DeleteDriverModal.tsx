import { useDeleteDriver } from '@/api/drivers';
import type { DriverRead } from '@/api/generated/types.gen';
import { ConfirmDeleteModal } from '@/pages/admin/routes/components/ConfirmDeleteModal';

interface DeleteDriverModalProps {
  driver: DriverRead;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onDeleted: () => void;
}

export function DeleteDriverModal({
  driver,
  open,
  onOpenChange,
  onDeleted,
}: DeleteDriverModalProps) {
  const remove = useDeleteDriver();
  return (
    <ConfirmDeleteModal
      open={open}
      onOpenChange={onOpenChange}
      title="Delete Driver"
      description={`Are you sure you want to delete ${driver.full_name}? This action cannot be undone.`}
      isPending={remove.isPending}
      isError={remove.isError}
      errorMessage="Couldn't delete this driver."
      onConfirm={() =>
        remove.mutate(
          { path: { driver_id: driver.driver_id } },
          { onSuccess: onDeleted }
        )
      }
    />
  );
}
