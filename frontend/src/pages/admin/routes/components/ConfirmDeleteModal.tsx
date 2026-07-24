import type { ReactNode } from 'react';

import {
  Button,
  FieldDescription,
  Modal,
  ModalContent,
  ModalDescription,
  ModalHeader,
  ModalTitle,
} from '@/common/components';

interface ConfirmDeleteModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** Dialog heading, e.g. "Delete Route Group". */
  title: string;
  /** Body copy describing what will be deleted. */
  description: ReactNode;
  /** Disables the actions while the delete request is in flight. */
  isPending?: boolean;
  /** Shows the error message when the delete request failed. */
  isError?: boolean;
  /** Error copy shown on failure; the caller phrases the noun. */
  errorMessage?: string;
  /** Runs the delete. Closing on success is the caller's job. */
  onConfirm: () => void;
}

/**
 * Shared confirmation dialog for the routes admin delete actions (groups,
 * routes, addresses). Presentational only: the caller owns the delete
 * mutation and passes its title/description, pending/error state, and confirm
 * handler.
 */
export function ConfirmDeleteModal({
  open,
  onOpenChange,
  title,
  description,
  isPending = false,
  isError = false,
  errorMessage = 'Something went wrong. Please try again.',
  onConfirm,
}: ConfirmDeleteModalProps) {
  return (
    <Modal open={open} onOpenChange={onOpenChange}>
      <ModalContent>
        <ModalHeader>
          <ModalTitle>{title}</ModalTitle>
          <ModalDescription>{description}</ModalDescription>
        </ModalHeader>

        <div className="flex items-center justify-end gap-4">
          {isError && <FieldDescription error>{errorMessage}</FieldDescription>}
          <Button
            variant="tertiary"
            onClick={() => onOpenChange(false)}
            disabled={isPending}
          >
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={onConfirm}
            disabled={isPending}
          >
            Delete
          </Button>
        </div>
      </ModalContent>
    </Modal>
  );
}
