import { ConfirmModal } from '@/common/components';

interface NoteDeleteConfirmModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
  isLoading?: boolean;
  error?: string | null;
}

export function NoteDeleteConfirmModal({
  open,
  onOpenChange,
  onConfirm,
  isLoading = false,
  error = null,
}: NoteDeleteConfirmModalProps) {
  return (
    <ConfirmModal
      open={open}
      onOpenChange={onOpenChange}
      onConfirm={onConfirm}
      title="Delete note?"
      description="Once you delete a note, it cannot be recovered."
      confirmLabel={isLoading ? 'Deleting\u2026' : 'Delete'}
      confirmVariant="destructive"
      isLoading={isLoading}
      error={error}
    />
  );
}
