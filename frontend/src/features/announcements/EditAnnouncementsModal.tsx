import {
  Button,
  Modal,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalTitle,
} from '@/common/components';
import type { Announcement } from '@/types/announcement';

import { EditAnnouncementRow } from './EditAnnouncementRow';

interface EditAnnouncementsModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  announcements: Announcement[];
  currentUserId: string;
  pendingDeleteIds: Set<string>;
  onToggleDelete: (announcement: Announcement) => void;
  onCancel: () => void;
  onSave: () => void;
  onAddNew: () => void;
  isSaving?: boolean;
}

export function EditAnnouncementsModal({
  open,
  onOpenChange,
  announcements,
  currentUserId,
  pendingDeleteIds,
  onToggleDelete,
  onCancel,
  onSave,
  onAddNew,
  isSaving = false,
}: EditAnnouncementsModalProps) {
  const hasPendingDeletes = pendingDeleteIds.size > 0;

  return (
    <Modal open={open} onOpenChange={onOpenChange}>
      <ModalContent className="flex max-h-[min(720px,90vh)] max-w-[600px] flex-col gap-4 p-6">
        <ModalHeader className="shrink-0 gap-0">
          <ModalTitle>Edit Announcements</ModalTitle>
        </ModalHeader>

        <div className="border-grey-300 min-h-0 flex-1 overflow-y-auto rounded-2xl border p-4">
          <ul className="flex flex-col gap-6">
            {announcements.map((announcement) => (
              <li key={announcement.announcement_id}>
                <EditAnnouncementRow
                  announcement={announcement}
                  currentUserId={currentUserId}
                  pendingDelete={pendingDeleteIds.has(
                    announcement.announcement_id
                  )}
                  onToggleDelete={onToggleDelete}
                />
              </li>
            ))}
          </ul>
        </div>

        <ModalFooter className="mt-2 shrink-0 items-center">
          <Button
            type="button"
            variant="secondary"
            onClick={onCancel}
            disabled={isSaving}
          >
            Cancel
          </Button>
          <div className="flex gap-3">
            <Button
              type="button"
              variant="secondary"
              onClick={onSave}
              disabled={isSaving || !hasPendingDeletes}
            >
              {isSaving ? 'Saving…' : 'Save'}
            </Button>
            <Button type="button" onClick={onAddNew} disabled={isSaving}>
              Add New
            </Button>
          </div>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}
