import {
  Button,
  Modal,
  ModalContent,
  ModalDescription,
  ModalFooter,
  ModalHeader,
  ModalTitle,
} from '@/common/components';

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
    <Modal open={open} onOpenChange={onOpenChange}>
      <ModalContent className="max-w-[480px]">
        <ModalHeader>
          <ModalTitle variant="confirmation">Delete note?</ModalTitle>
          <ModalDescription>
            Once you delete a note, it cannot be recovered.
          </ModalDescription>
        </ModalHeader>
        {error && (
          <p className="text-p2 text-red" role="alert">
            {error}
          </p>
        )}
        <ModalFooter>
          <Button
            type="button"
            variant="secondary"
            onClick={() => onOpenChange(false)}
            disabled={isLoading}
          >
            Cancel
          </Button>
          <Button
            type="button"
            variant="destructive"
            onClick={onConfirm}
            disabled={isLoading}
          >
            {isLoading ? 'Deleting…' : 'Delete'}
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}
