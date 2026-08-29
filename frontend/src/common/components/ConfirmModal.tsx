import type * as React from 'react';

import { Button } from './Button';
import {
  Modal,
  ModalContent,
  ModalDescription,
  ModalFooter,
  ModalHeader,
  ModalTitle,
} from './Modal';

interface ConfirmModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
  title: string;
  description: React.ReactNode;
  /** Label for the confirming button, e.g. "Duplicate anyway". */
  confirmLabel: string;
  confirmVariant?: 'primary' | 'destructive';
  cancelLabel?: string;
  isLoading?: boolean;
  /** Shown above the footer when the confirmed action failed. */
  error?: string | null;
}

/**
 * Yes/no dialog for an action worth a second look: a short title, a sentence
 * explaining the consequence, and Cancel / confirm.
 */
export function ConfirmModal({
  open,
  onOpenChange,
  onConfirm,
  title,
  description,
  confirmLabel,
  confirmVariant = 'primary',
  cancelLabel = 'Cancel',
  isLoading = false,
  error = null,
}: ConfirmModalProps) {
  return (
    <Modal open={open} onOpenChange={onOpenChange}>
      <ModalContent className="max-w-[480px]">
        <ModalHeader>
          <ModalTitle variant="confirmation">{title}</ModalTitle>
          <ModalDescription>{description}</ModalDescription>
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
            {cancelLabel}
          </Button>
          <Button
            type="button"
            variant={confirmVariant}
            onClick={onConfirm}
            disabled={isLoading}
          >
            {confirmLabel}
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}
