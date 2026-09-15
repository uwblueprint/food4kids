import {
  Button,
  Modal,
  ModalContent,
  ModalDescription,
  ModalFooter,
  ModalHeader,
  ModalTitle,
} from '@/common/components';

interface UnsavedChangesModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onDiscard: () => void;
  onKeepEditing: () => void;
}

export function UnsavedChangesModal({
  open,
  onOpenChange,
  onDiscard,
  onKeepEditing,
}: UnsavedChangesModalProps) {
  return (
    <Modal open={open} onOpenChange={onOpenChange}>
      <ModalContent className="gap-6">
        <ModalHeader>
          <ModalTitle variant="confirmation">Unsaved changes</ModalTitle>
          <ModalDescription className="text-p1 text-grey-500 min-h-[48px] font-medium">
            Are you sure you want to go back to the home screen?
          </ModalDescription>
        </ModalHeader>
        <ModalFooter className="justify-end gap-2">
          <Button
            className="tablet:w-[139.5px] w-[139.5px]"
            type="button"
            variant="secondary"
            onClick={onDiscard}
          >
            Discard changes
          </Button>
          <Button
            className="tablet:w-[139.5px] w-[139.5px]"
            type="button"
            variant="primary"
            onClick={onKeepEditing}
          >
            Keep editing
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}
