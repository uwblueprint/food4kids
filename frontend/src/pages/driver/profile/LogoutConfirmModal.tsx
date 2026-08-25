import {
  Button,
  Modal,
  ModalContent,
  ModalDescription,
  ModalFooter,
  ModalHeader,
  ModalTitle,
} from '@/common/components';

interface LogoutConfirmModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
  isLoading?: boolean;
}

export function LogoutConfirmModal({
  open,
  onOpenChange,
  onConfirm,
  isLoading = false,
}: LogoutConfirmModalProps) {
  return (
    <Modal open={open} onOpenChange={onOpenChange}>
      <ModalContent className="gap-6">
        <ModalHeader>
          <ModalTitle variant="confirmation">Log out</ModalTitle>
          <ModalDescription className="text-p1 text-grey-500 min-h-[48px] font-medium">
            Are you sure you would like to log out of your account?
          </ModalDescription>
        </ModalHeader>
        <ModalFooter className="justify-end gap-2">
          <Button
            className="tablet:w-[139.5px] w-[139.5px]"
            type="button"
            variant="secondary"
            onClick={() => onOpenChange(false)}
            disabled={isLoading}
          >
            Go back
          </Button>
          <Button
            className="tablet:w-[139.5px] w-[139.5px]"
            type="button"
            variant="primary"
            onClick={onConfirm}
            disabled={isLoading}
          >
            Log out
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}
