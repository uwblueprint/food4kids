import { ConfirmModal } from '@/common/components';

export type ConfirmModalVariant = 'delete' | 'save' | 'unsaved';

interface AnnouncementConfirmModalProps {
  open: boolean;
  variant: ConfirmModalVariant;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
  isLoading?: boolean;
}

const COPY: Record<
  ConfirmModalVariant,
  {
    title: string;
    description: string;
    confirm: string;
    confirmVariant: 'primary' | 'destructive';
  }
> = {
  delete: {
    title: 'Delete announcement?',
    description: 'Once you delete an announcement, it cannot be recovered.',
    confirm: 'Delete',
    confirmVariant: 'destructive',
  },
  save: {
    title: 'Save changes?',
    description: 'All edits to the announcement board will be saved.',
    confirm: 'Save',
    confirmVariant: 'primary',
  },
  unsaved: {
    title: 'Are you sure?',
    description: 'If you leave now your changes will be unsaved.',
    confirm: 'Leave',
    confirmVariant: 'primary',
  },
};

export function AnnouncementConfirmModal({
  open,
  variant,
  onOpenChange,
  onConfirm,
  isLoading = false,
}: AnnouncementConfirmModalProps) {
  const copy = COPY[variant];

  return (
    <ConfirmModal
      open={open}
      onOpenChange={onOpenChange}
      onConfirm={onConfirm}
      title={copy.title}
      description={copy.description}
      confirmLabel={isLoading ? 'Working\u2026' : copy.confirm}
      confirmVariant={copy.confirmVariant}
      isLoading={isLoading}
    />
  );
}
