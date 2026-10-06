import { useDeleteDriver } from '@/api/drivers';
import type { DriverRead } from '@/api/generated/types.gen';
import { ConfirmModal } from '@/common/components';

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
    <ConfirmModal
      open={open}
      onOpenChange={onOpenChange}
      title="Delete Driver"
      description={`Are you sure you want to delete ${driver.full_name}? This action cannot be undone.`}
      confirmLabel="Delete"
      confirmVariant="destructive"
      isLoading={remove.isPending}
      error={remove.isError ? "Couldn't delete this driver." : null}
      onConfirm={() =>
        remove.mutate(
          { path: { driver_id: driver.driver_id } },
          { onSuccess: onDeleted }
        )
      }
    />
  );
}
