import { useState } from 'react';

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

import { AnnouncementFormModal } from './AnnouncementFormModal';
import { AnnouncementsPanel } from './AnnouncementsPanel';
import { useBootstrapCurrentUser } from './useBootstrapCurrentUser';

interface AnnouncementsBoardProps {
  /** Override role when not using route-based layout (optional). */
  role?: 'admin' | 'driver';
}

export function AnnouncementsBoard({ role: roleOverride }: AnnouncementsBoardProps) {
  const { user } = useAuth();
  const role = roleOverride ?? user.role;
  useBootstrapCurrentUser(role);

  const [panelOpen, setPanelOpen] = useState(false);
  const [formOpen, setFormOpen] = useState(false);
  const [formMode, setFormMode] = useState<'create' | 'edit'>('create');
  const [editingAnnouncement, setEditingAnnouncement] = useState<
    Announcement | undefined
  >();

  const { data: announcements = [], isLoading } = useAnnouncements();
  const createMutation = useCreateAnnouncement();
  const updateMutation = useUpdateAnnouncement();
  const deleteMutation = useDeleteAnnouncement();

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

  const handleDelete = async (announcement: Announcement) => {
    const confirmed = window.confirm(
      `Delete "${announcement.subject}"? This cannot be undone.`
    );
    if (!confirmed) return;
    await deleteMutation.mutateAsync(announcement.announcement_id);
  };

  const handleFormSubmit = async (values: {
    subject: string;
    message: string;
  }) => {
    if (!user.userId) {
      throw new Error(
        'Missing user id. Seed the database (docker-compose exec backend python -m app.seed_database), set VITE_DEV_USER_ID in frontend/.env to a users.user_id value, or log in once auth is wired.'
      );
    }
    if (formMode === 'create') {
      await createMutation.mutateAsync({
        user_id: user.userId,
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

  const isSubmitting =
    createMutation.isPending || updateMutation.isPending;

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
        role={role}
        onCreateClick={openCreateForm}
        onEdit={openEditForm}
        onDelete={handleDelete}
      />

      <AnnouncementFormModal
        open={formOpen}
        onOpenChange={setFormOpen}
        mode={formMode}
        announcement={editingAnnouncement}
        onSubmit={handleFormSubmit}
        isSubmitting={isSubmitting}
      />
    </>
  );
}
