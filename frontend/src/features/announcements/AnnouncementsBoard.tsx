<<<<<<< HEAD
import { useCallback, useState } from 'react';
=======
import { useState } from 'react';
>>>>>>> fa70cf5 (add board and crud functionality)

import MegaphoneIcon from '@/assets/icons/megaphone.svg?react';
import {
  useAnnouncements,
  useCreateAnnouncement,
  useDeleteAnnouncement,
  useUpdateAnnouncement,
} from '@/api/announcements';
import { Button } from '@/common/components';
import { useAuth } from '@/contexts/AuthContext';
import type { Announcement } from '@/types/announcement';

<<<<<<< HEAD
import { AnnouncementConfirmModal } from './AnnouncementConfirmModal';
import { AnnouncementFormModal } from './AnnouncementFormModal';
import {
  AnnouncementsPanel,
  PANEL_WIDTH_DEFAULT,
} from './AnnouncementsPanel';
import { EditAnnouncementsModal } from './EditAnnouncementsModal';
import { PANEL_WIDTH_MAX, PANEL_WIDTH_MIN } from './utils';
import { useAnnouncementReads } from './useAnnouncementReads';
=======
import { AnnouncementFormModal } from './AnnouncementFormModal';
import { AnnouncementsPanel } from './AnnouncementsPanel';
import { useBootstrapCurrentUser } from './useBootstrapCurrentUser';
>>>>>>> fa70cf5 (add board and crud functionality)

interface AnnouncementsBoardProps {
  /** Override role when not using route-based layout (optional). */
  role?: 'admin' | 'driver';
}

<<<<<<< HEAD
type ConfirmState =
  | { type: 'delete'; announcement: Announcement }
  | { type: 'save-edit-board' }
  | { type: 'unsaved-edit-board' };

export function AnnouncementsBoard({ role: roleOverride }: AnnouncementsBoardProps) {
  const { user } = useAuth();
  const role = roleOverride ?? user.role;

  const [panelOpen, setPanelOpen] = useState(false);
  const [panelWidth, setPanelWidth] = useState(PANEL_WIDTH_DEFAULT);
=======
export function AnnouncementsBoard({ role: roleOverride }: AnnouncementsBoardProps) {
  const { user } = useAuth();
  const role = roleOverride ?? user.role;
  useBootstrapCurrentUser(role);

  const [panelOpen, setPanelOpen] = useState(false);
>>>>>>> fa70cf5 (add board and crud functionality)
  const [formOpen, setFormOpen] = useState(false);
  const [formMode, setFormMode] = useState<'create' | 'edit'>('create');
  const [editingAnnouncement, setEditingAnnouncement] = useState<
    Announcement | undefined
  >();
<<<<<<< HEAD
  const [editBoardOpen, setEditBoardOpen] = useState(false);
  const [pendingDeleteIds, setPendingDeleteIds] = useState<Set<string>>(
    () => new Set()
  );
  const [confirmState, setConfirmState] = useState<ConfirmState | null>(null);

  const { readIds, markAsRead } = useAnnouncementReads(user.userId);
=======

>>>>>>> fa70cf5 (add board and crud functionality)
  const { data: announcements = [], isLoading } = useAnnouncements();
  const createMutation = useCreateAnnouncement();
  const updateMutation = useUpdateAnnouncement();
  const deleteMutation = useDeleteAnnouncement();

<<<<<<< HEAD
  const hasPendingDeletes = pendingDeleteIds.size > 0;

  const clampPanelWidth = useCallback((width: number) => {
    return Math.min(PANEL_WIDTH_MAX, Math.max(PANEL_WIDTH_MIN, width));
  }, []);

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

=======
>>>>>>> fa70cf5 (add board and crud functionality)
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

<<<<<<< HEAD
  const handleDeleteRequest = (announcement: Announcement) => {
    setConfirmState({ type: 'delete', announcement });
  };

  const handleConfirmDelete = async () => {
    if (!confirmState || confirmState.type !== 'delete') return;
    await deleteMutation.mutateAsync(confirmState.announcement.announcement_id);
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
      await deleteMutation.mutateAsync(announcementId);
    }
    resetEditBoardState();
    setConfirmState(null);
  };

  const handleConfirmDiscardEditBoard = () => {
    resetEditBoardState();
    setConfirmState(null);
=======
  const handleDelete = async (announcement: Announcement) => {
    const confirmed = window.confirm(
      `Delete "${announcement.subject}"? This cannot be undone.`
    );
    if (!confirmed) return;
    await deleteMutation.mutateAsync(announcement.announcement_id);
>>>>>>> fa70cf5 (add board and crud functionality)
  };

  const handleFormSubmit = async (values: {
    subject: string;
    message: string;
<<<<<<< HEAD
    sendEmailToAll: boolean;
  }) => {
    void values.sendEmailToAll;

    if (formMode === 'create') {
      await createMutation.mutateAsync({
=======
  }) => {
    if (!user.userId) {
      throw new Error(
        'Missing user id. Seed the database (docker-compose exec backend python -m app.seed_database), set VITE_DEV_USER_ID in frontend/.env to a users.user_id value, or log in once auth is wired.'
      );
    }
    if (formMode === 'create') {
      await createMutation.mutateAsync({
        user_id: user.userId,
>>>>>>> fa70cf5 (add board and crud functionality)
        subject: values.subject,
        message: values.message,
        attachments: [],
      });
    } else if (editingAnnouncement) {
      await updateMutation.mutateAsync({
        announcementId: editingAnnouncement.announcement_id,
        payload: {
          subject: values.subject,
          message: values.message,
        },
      });
    }
  };

<<<<<<< HEAD
  const handleAnnouncementOpen = (announcement: Announcement) => {
    markAsRead(announcement.announcement_id);
  };

  const isSubmitting =
    createMutation.isPending ||
    updateMutation.isPending ||
    deleteMutation.isPending;
=======
  const isSubmitting =
    createMutation.isPending || updateMutation.isPending;
>>>>>>> fa70cf5 (add board and crud functionality)

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
        currentUserId={user.userId}
<<<<<<< HEAD
        readIds={readIds}
        role={role}
        panelWidth={panelWidth}
        onPanelWidthChange={(width) => setPanelWidth(clampPanelWidth(width))}
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
        currentUserId={user.userId}
        pendingDeleteIds={pendingDeleteIds}
        onToggleDelete={handleToggleEditBoardDelete}
        onCancel={requestCloseEditBoard}
        onSave={handleSaveEditBoardRequest}
        onAddNew={openCreateForm}
        isSaving={deleteMutation.isPending}
=======
        role={role}
        onCreateClick={openCreateForm}
        onEdit={openEditForm}
        onDelete={handleDelete}
>>>>>>> fa70cf5 (add board and crud functionality)
      />

      <AnnouncementFormModal
        open={formOpen}
        onOpenChange={setFormOpen}
        mode={formMode}
<<<<<<< HEAD
        role={role}
=======
>>>>>>> fa70cf5 (add board and crud functionality)
        announcement={editingAnnouncement}
        onSubmit={handleFormSubmit}
        isSubmitting={isSubmitting}
      />
<<<<<<< HEAD

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
=======
>>>>>>> fa70cf5 (add board and crud functionality)
    </>
  );
}
