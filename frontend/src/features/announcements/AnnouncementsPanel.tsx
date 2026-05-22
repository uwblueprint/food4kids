import { useEffect } from 'react';

import RightPanelCloseIcon from '@/assets/icons/right-panel-close.svg?react';
import { Button, Spinner } from '@/common/components';
import { cn } from '@/lib/utils';
import type { Announcement } from '@/types/announcement';

import { AnnouncementCard } from './AnnouncementCard';
import { AnnouncementsEmptyState } from './AnnouncementsEmptyState';
import { canManageAnnouncement } from './utils';

interface AnnouncementsPanelProps {
  open: boolean;
  onClose: () => void;
  announcements: Announcement[];
  isLoading: boolean;
  currentUserId: string;
  role: 'admin' | 'driver';
  onCreateClick: () => void;
  onEdit: (announcement: Announcement) => void;
  onDelete: (announcement: Announcement) => void;
}

export function AnnouncementsPanel({
  open,
  onClose,
  announcements,
  isLoading,
  currentUserId,
  role,
  onCreateClick,
  onEdit,
  onDelete,
}: AnnouncementsPanelProps) {
  useEffect(() => {
    if (!open) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <>
      <button
        type="button"
        aria-label="Close announcements"
        className="fixed inset-0 z-40 bg-black/40 md:bg-black/30"
        onClick={onClose}
      />
      <aside
        className={cn(
          'bg-grey-100 fixed z-50 flex flex-col shadow-harsh',
          'inset-0 md:inset-y-0 md:right-0 md:left-auto md:w-full md:max-w-[420px]',
          'md:rounded-l-2xl'
        )}
        role="dialog"
        aria-modal="true"
        aria-labelledby="announcements-panel-title"
      >
        <header className="border-grey-300 flex shrink-0 items-center justify-between border-b px-5 py-4 md:px-6">
          <h2
            id="announcements-panel-title"
            className="text-h1 text-grey-500 font-bold"
          >
            Announcements
          </h2>
          <Button
            type="button"
            variant="tertiary"
            shape="circular"
            onClick={onClose}
            aria-label="Close announcements panel"
          >
            <RightPanelCloseIcon className="size-5 text-blue-300" />
          </Button>
        </header>

        <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
          {isLoading ? (
            <div className="flex flex-1 items-center justify-center py-16">
              <Spinner />
            </div>
          ) : announcements.length === 0 ? (
            <AnnouncementsEmptyState onCreateClick={onCreateClick} />
          ) : (
            <ul className="flex flex-1 flex-col gap-4 overflow-y-auto px-5 py-4 md:px-6">
              {announcements.map((announcement) => (
                <li key={announcement.announcement_id}>
                  <AnnouncementCard
                    announcement={announcement}
                    currentUserId={currentUserId}
                    canManage={canManageAnnouncement(
                      announcement,
                      currentUserId,
                      role
                    )}
                    onEdit={onEdit}
                    onDelete={onDelete}
                  />
                </li>
              ))}
            </ul>
          )}
        </div>

        {announcements.length > 0 && (
          <footer className="border-grey-300 shrink-0 border-t p-5 md:p-6">
            <Button
              type="button"
              className="w-full"
              onClick={onCreateClick}
            >
              Create Announcement
            </Button>
          </footer>
        )}
      </aside>
    </>
  );
}
