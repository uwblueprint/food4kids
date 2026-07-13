import { useState } from 'react';

import {
  useAnnouncements,
  useCreateAnnouncement,
  useDeleteAnnouncement,
  useSendAnnouncementEmail,
  useUpdateAnnouncement,
} from '@/api/announcements';
import MegaphoneIcon from '@/assets/icons/megaphone.svg?react';
import { Button } from '@/common/components';
import type { Announcement } from '@/types/announcement';

import { AnnouncementConfirmModal } from './AnnouncementConfirmModal';
import { AnnouncementFormModal } from './AnnouncementFormModal';
import { AnnouncementsPanel } from './AnnouncementsPanel';
import { EditAnnouncementsModal } from './EditAnnouncementsModal';
import { useAnnouncementReads } from './useAnnouncementReads';
import { roleFromStoredToken } from './utils';

type ConfirmState =
  | { type: 'delete'; announcement: Announcement }
  | { type: 'save-edit-board' }
  | { type: 'unsaved-edit-board' };

export function AnnouncementsBoard() {
  const role = roleFromStoredToken();
  const currentUserId = '';

  const [panelOpen, setPanelOpen] = useState(false);
  const [formOpen, setFormOpen] = useState(false);
  const [formMode, setFormMode] = useState<'create' | 'edit'>('create');
  const [editingAnnouncement, setEditingAnnouncement] = useState<
    Announcement | undefined
  >();
  const [editBoardOpen, setEditBoardOpen] = useState(false);
  const [pendingDeleteIds, setPendingDeleteIds] = useState<Set<string>>(
    () => new Set()
  );
  const [confirmState, setConfirmState] = useState<ConfirmState | null>(null);

  const { readIds, markAsRead } = useAnnouncementReads(currentUserId);
  const { data: announcements = [], isLoading } = useAnnouncements();
  const createMutation = useCreateAnnouncement();
  const updateMutation = useUpdateAnnouncement();
  const deleteMutation = useDeleteAnnouncement();
  const sendEmailMutation = useSendAnnouncementEmail();

  const hasPendingDeletes = pendingDeleteIds.size > 0;

  const resetEditBoardState = () => {
    setEditBoardOpen(false);
    setPendingDeleteIds(new Set());
  };

  const requestCloseEditBoard = () => {
    if (hasPendingDeletes) {
      setConfirmState({ type: 'unsaved-edit-board' });
      return;
    }
    resetEditBoardState();
  };

  const openCreateForm = () => {
    setFormMode('create');
    setEditingAnnouncement(undefined);
    setFormOpen(true);
  };

  const openEditForm = (announcement: Announcement) => {
    setFormMode('edit');
    setEditingAnnouncement(announcement);
    setFormOpen(true);
  };

  const handleDeleteRequest = (announcement: Announcement) => {
    setConfirmState({ type: 'delete', announcement });
  };

  const handleConfirmDelete = async () => {
    if (!confirmState || confirmState.type !== 'delete') return;
    await deleteMutation.mutateAsync({
      path: { announcement_id: confirmState.announcement.announcement_id },
    });
    setConfirmState(null);
  };

  const handleToggleEditBoardDelete = (announcement: Announcement) => {
    setPendingDeleteIds((previous) => {
      const next = new Set(previous);
      if (next.has(announcement.announcement_id)) {
        next.delete(announcement.announcement_id);
      } else {
        next.add(announcement.announcement_id);
      }
      return next;
    });
  };

  const handleSaveEditBoardRequest = () => {
    if (!hasPendingDeletes) return;
    setConfirmState({ type: 'save-edit-board' });
  };

  const handleConfirmSaveEditBoard = async () => {
    const ids = [...pendingDeleteIds];
    for (const announcementId of ids) {
      await deleteMutation.mutateAsync({
        path: { announcement_id: announcementId },
      });
    }
    resetEditBoardState();
    setConfirmState(null);
  };

  const handleConfirmDiscardEditBoard = () => {
    resetEditBoardState();
    setConfirmState(null);
  };

  const handleFormSubmit = async (values: {
    subject: string;
    message: string;
    sendEmailToAll: boolean;
  }) => {
    if (formMode === 'create') {
      const created = await createMutation.mutateAsync({
        body: {
          subject: values.subject,
          message: values.message,
          attachments: [],
        },
      });

      if (values.sendEmailToAll && role === 'admin') {
        const result = await sendEmailMutation.mutateAsync({
          path: { announcement_id: created.announcement_id },
        });
        if (result.failed > 0) {
          throw new Error(
            `Announcement posted, but ${result.failed} email(s) failed to send.`
          );
        }
      }
    } else if (editingAnnouncement) {
      await updateMutation.mutateAsync({
        path: { announcement_id: editingAnnouncement.announcement_id },
        body: {
          subject: values.subject,
          message: values.message,
        },
      });
    }
  };

  const handleAnnouncementOpen = (announcement: Announcement) => {
    markAsRead(announcement.announcement_id);
  };

  const isSubmitting =
    createMutation.isPending ||
    updateMutation.isPending ||
    deleteMutation.isPending ||
    sendEmailMutation.isPending;

  return (
    <>
      <Button
        type="button"
        variant="tertiary"
        shape="circular"
        aria-label="Open announcements"
        onClick={() => setPanelOpen(true)}
      >
        <MegaphoneIcon className="size-5 text-blue-300" />
      </Button>

      <AnnouncementsPanel
        open={panelOpen}
        onClose={() => setPanelOpen(false)}
        announcements={announcements}
        isLoading={isLoading}
        currentUserId={currentUserId}
        readIds={readIds}
        role={role}
        onCreateClick={openCreateForm}
        onEditBoardClick={() => setEditBoardOpen(true)}
        onAnnouncementOpen={handleAnnouncementOpen}
        onEdit={openEditForm}
        onDelete={handleDeleteRequest}
      />

      <EditAnnouncementsModal
        open={editBoardOpen}
        onOpenChange={(open) => {
          if (!open) requestCloseEditBoard();
        }}
        announcements={announcements}
        currentUserId={currentUserId}
        pendingDeleteIds={pendingDeleteIds}
        onToggleDelete={handleToggleEditBoardDelete}
        onCancel={requestCloseEditBoard}
        onSave={handleSaveEditBoardRequest}
        onAddNew={openCreateForm}
        isSaving={deleteMutation.isPending}
      />

      <AnnouncementFormModal
        open={formOpen}
        onOpenChange={setFormOpen}
        mode={formMode}
        role={role}
        announcement={editingAnnouncement}
        onSubmit={handleFormSubmit}
        isSubmitting={isSubmitting}
      />

      <AnnouncementConfirmModal
        open={confirmState?.type === 'delete'}
        variant="delete"
        onOpenChange={(open) => {
          if (!open) setConfirmState(null);
        }}
        onConfirm={handleConfirmDelete}
        isLoading={deleteMutation.isPending}
      />

      <AnnouncementConfirmModal
        open={confirmState?.type === 'save-edit-board'}
        variant="save"
        onOpenChange={(open) => {
          if (!open) setConfirmState(null);
        }}
        onConfirm={handleConfirmSaveEditBoard}
        isLoading={deleteMutation.isPending}
      />

      <AnnouncementConfirmModal
        open={confirmState?.type === 'unsaved-edit-board'}
        variant="unsaved"
        onOpenChange={(open) => {
          if (!open) setConfirmState(null);
        }}
        onConfirm={handleConfirmDiscardEditBoard}
      />
    </>
  );
}
