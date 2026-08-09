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
          <ModalTitle className="text-h2">Log out</ModalTitle>
          <ModalDescription className="text-p1 text-grey-500 font-medium min-h-[48px]">
            Are you sure you would like to log out of your account?
          </ModalDescription>
        </ModalHeader>
        <ModalFooter className="gap-2 justify-end">
          <Button
            className="w-[139.5px] tablet:w-[139.5px]"
            type="button"
            variant="secondary"
            onClick={() => onOpenChange(false)}
            disabled={isLoading}
          >
            Go back
          </Button>
          <Button
            className="w-[139.5px] tablet:w-[139.5px]"
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
