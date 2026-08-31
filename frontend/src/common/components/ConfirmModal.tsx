import type * as React from 'react';

import { Button } from './Button';
import { FieldDescription } from './Field';
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
  /** Disables both actions while the confirmed action is in flight. */
  isLoading?: boolean;
  /** Shown beside the actions when the confirmed action failed. */
  error?: React.ReactNode;
}

/**
 * The confirmation dialog: a short title, one sentence on the consequence,
 * and Cancel / confirm. Per the design system's modal specs, the actions are
 * grouped on the right with a grey secondary Cancel, and the layout inherits
 * ModalContent's 600px width.
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
      <ModalContent>
        <ModalHeader>
          <ModalTitle variant="confirmation">{title}</ModalTitle>
          <ModalDescription>{description}</ModalDescription>
        </ModalHeader>
        <ModalFooter className="items-center justify-end gap-4">
          {error && <FieldDescription error>{error}</FieldDescription>}
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
