<<<<<<< HEAD
<<<<<<< HEAD
import { useCallback, useState } from 'react';
=======
import { useState } from 'react';
>>>>>>> fa70cf5 (add board and crud functionality)
=======
import { useCallback, useState } from 'react';
>>>>>>> b56351b (add bulk edit modal)

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
=======
import { AnnouncementConfirmModal } from './AnnouncementConfirmModal';
import { AnnouncementFormModal } from './AnnouncementFormModal';
import {
  AnnouncementsPanel,
  PANEL_WIDTH_DEFAULT,
} from './AnnouncementsPanel';
import { EditAnnouncementsModal } from './EditAnnouncementsModal';
import { PANEL_WIDTH_MAX, PANEL_WIDTH_MIN } from './utils';
import { useAnnouncementReads } from './useAnnouncementReads';
>>>>>>> b56351b (add bulk edit modal)

interface AnnouncementsBoardProps {
  /** Override role when not using route-based layout (optional). */
  role?: 'admin' | 'driver';
}

<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> b56351b (add bulk edit modal)
type ConfirmState =
  | { type: 'delete'; announcement: Announcement }
  | { type: 'save-edit-board' }
  | { type: 'unsaved-edit-board' };

<<<<<<< HEAD
export function AnnouncementsBoard({ role: roleOverride }: AnnouncementsBoardProps) {
  const { user } = useAuth();
  const role = roleOverride ?? user.role;

  const [panelOpen, setPanelOpen] = useState(false);
  const [panelWidth, setPanelWidth] = useState(PANEL_WIDTH_DEFAULT);
=======
=======
>>>>>>> b56351b (add bulk edit modal)
export function AnnouncementsBoard({ role: roleOverride }: AnnouncementsBoardProps) {
  const { user } = useAuth();
  const role = roleOverride ?? user.role;

  const [panelOpen, setPanelOpen] = useState(false);
<<<<<<< HEAD
>>>>>>> fa70cf5 (add board and crud functionality)
=======
  const [panelWidth, setPanelWidth] = useState(PANEL_WIDTH_DEFAULT);
>>>>>>> b56351b (add bulk edit modal)
  const [formOpen, setFormOpen] = useState(false);
  const [formMode, setFormMode] = useState<'create' | 'edit'>('create');
  const [editingAnnouncement, setEditingAnnouncement] = useState<
    Announcement | undefined
  >();
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> b56351b (add bulk edit modal)
  const [editBoardOpen, setEditBoardOpen] = useState(false);
  const [pendingDeleteIds, setPendingDeleteIds] = useState<Set<string>>(
    () => new Set()
  );
  const [confirmState, setConfirmState] = useState<ConfirmState | null>(null);

  const { readIds, markAsRead } = useAnnouncementReads(user.userId);
<<<<<<< HEAD
=======

>>>>>>> fa70cf5 (add board and crud functionality)
=======
>>>>>>> b56351b (add bulk edit modal)
  const { data: announcements = [], isLoading } = useAnnouncements();
  const createMutation = useCreateAnnouncement();
  const updateMutation = useUpdateAnnouncement();
  const deleteMutation = useDeleteAnnouncement();

<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> b56351b (add bulk edit modal)
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

<<<<<<< HEAD
=======
>>>>>>> fa70cf5 (add board and crud functionality)
=======
>>>>>>> b56351b (add bulk edit modal)
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
<<<<<<< HEAD
=======
>>>>>>> b56351b (add bulk edit modal)
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
<<<<<<< HEAD
=======
  const handleDelete = async (announcement: Announcement) => {
    const confirmed = window.confirm(
      `Delete "${announcement.subject}"? This cannot be undone.`
    );
    if (!confirmed) return;
    await deleteMutation.mutateAsync(announcement.announcement_id);
>>>>>>> fa70cf5 (add board and crud functionality)
=======
>>>>>>> b56351b (add bulk edit modal)
  };

  const handleFormSubmit = async (values: {
    subject: string;
    message: string;
<<<<<<< HEAD
<<<<<<< HEAD
    sendEmailToAll: boolean;
  }) => {
    void values.sendEmailToAll;

<<<<<<< HEAD
    if (formMode === 'create') {
      await createMutation.mutateAsync({
=======
=======
    sendEmailToAll: boolean;
>>>>>>> b56351b (add bulk edit modal)
  }) => {
    void values.sendEmailToAll;

    if (!user.userId) {
      throw new Error(
        'Missing user id. After seeding, set VITE_DEV_USER_ID in frontend/.env to the seeded admin users.user_id (see seed output or query the users table).'
      );
    }
    if (formMode === 'create') {
      await createMutation.mutateAsync({
        user_id: user.userId,
>>>>>>> fa70cf5 (add board and crud functionality)
=======
    if (formMode === 'create') {
      await createMutation.mutateAsync({
>>>>>>> 5e0c3ad (use get_current_database_user_id as announcement user_id)
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
<<<<<<< HEAD
=======
>>>>>>> b56351b (add bulk edit modal)
  const handleAnnouncementOpen = (announcement: Announcement) => {
    markAsRead(announcement.announcement_id);
  };

<<<<<<< HEAD
  const isSubmitting =
    createMutation.isPending ||
    updateMutation.isPending ||
    deleteMutation.isPending;
=======
  const isSubmitting =
    createMutation.isPending || updateMutation.isPending;
>>>>>>> fa70cf5 (add board and crud functionality)
=======
  const isSubmitting =
    createMutation.isPending ||
    updateMutation.isPending ||
    deleteMutation.isPending;
>>>>>>> b56351b (add bulk edit modal)

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
=======
        readIds={readIds}
>>>>>>> b56351b (add bulk edit modal)
        role={role}
        panelWidth={panelWidth}
        onPanelWidthChange={(width) => setPanelWidth(clampPanelWidth(width))}
        onCreateClick={openCreateForm}
        onEditBoardClick={() => setEditBoardOpen(true)}
        onAnnouncementOpen={handleAnnouncementOpen}
        onEdit={openEditForm}
<<<<<<< HEAD
        onDelete={handleDelete}
>>>>>>> fa70cf5 (add board and crud functionality)
=======
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
>>>>>>> b56351b (add bulk edit modal)
      />

      <AnnouncementFormModal
        open={formOpen}
        onOpenChange={setFormOpen}
        mode={formMode}
<<<<<<< HEAD
<<<<<<< HEAD
        role={role}
=======
>>>>>>> fa70cf5 (add board and crud functionality)
=======
        role={role}
>>>>>>> b56351b (add bulk edit modal)
        announcement={editingAnnouncement}
        onSubmit={handleFormSubmit}
        isSubmitting={isSubmitting}
      />
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> b56351b (add bulk edit modal)

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
<<<<<<< HEAD
=======
>>>>>>> fa70cf5 (add board and crud functionality)
=======
>>>>>>> b56351b (add bulk edit modal)
    </>
  );
}
