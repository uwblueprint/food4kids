import { useEffect } from 'react';

import RightPanelCloseIcon from '@/assets/icons/right-panel-close.svg?react';
import { Button, Spinner } from '@/common/components';
import { cn } from '@/lib/utils';
import type { Announcement } from '@/types/announcement';

import { AnnouncementCard } from './AnnouncementCard';
import { AnnouncementsEmptyState } from './AnnouncementsEmptyState';
import {
  canManageAnnouncement,
  PANEL_CARD_GAP,
  PANEL_PADDING_BOTTOM,
  PANEL_PADDING_TOP,
  PANEL_PADDING_X,
  PANEL_SECTION_GAP,
  PANEL_WIDTH,
} from './utils';

interface AnnouncementsPanelProps {
  open: boolean;
  onClose: () => void;
  announcements: Announcement[];
  isLoading: boolean;
  currentUserId: string;
  readIds: Set<string>;
  role: 'admin' | 'driver';
  onCreateClick: () => void;
  onEditBoardClick: () => void;
  onAnnouncementOpen: (announcement: Announcement) => void;
  onEdit: (announcement: Announcement) => void;
  onDelete: (announcement: Announcement) => void;
}

export function AnnouncementsPanel({
  open,
  onClose,
  announcements,
  isLoading,
  currentUserId,
  readIds,
  role,
  onCreateClick,
  onEditBoardClick,
  onAnnouncementOpen,
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

  const hasAnnouncements = announcements.length > 0;

  return (
    <>
      <button
        type="button"
        aria-label="Close announcements"
        className="fixed inset-0 z-40 bg-black/40"
        onClick={onClose}
      />
      <aside
        className={cn(
          'bg-grey-150 shadow-harsh fixed top-0 right-0 z-50 flex h-dvh flex-col',
          'w-full max-w-[var(--announcements-panel-width)] rounded-l-2xl'
        )}
        style={
          {
            '--announcements-panel-width': `${PANEL_WIDTH}px`,
          } as React.CSSProperties
        }
        role="dialog"
        aria-modal="true"
        aria-labelledby="announcements-panel-title"
      >
        <header
          className={cn(
            'border-grey-300 bg-grey-150 flex shrink-0 items-center justify-between border-b',
            PANEL_PADDING_X,
            PANEL_PADDING_TOP,
            'pb-4'
          )}
        >
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
            <div
              className={cn(
                'flex flex-1 items-center justify-center',
                PANEL_PADDING_X,
                PANEL_SECTION_GAP
              )}
            >
              <Spinner />
            </div>
          ) : !hasAnnouncements ? (
            <AnnouncementsEmptyState onCreateClick={onCreateClick} />
          ) : (
            <div
              className={cn(
                'min-h-0 flex-1 overflow-y-auto',
                PANEL_PADDING_X,
                PANEL_SECTION_GAP
              )}
            >
              <ul className={cn('flex flex-col', PANEL_CARD_GAP)}>
                {announcements.map((announcement) => (
                  <li key={announcement.announcement_id}>
                    <AnnouncementCard
                      announcement={announcement}
                      currentUserId={currentUserId}
                      readIds={readIds}
                      canManage={canManageAnnouncement(
                        announcement,
                        currentUserId,
                        role
                      )}
                      onOpen={onAnnouncementOpen}
                      onEdit={onEdit}
                      onDelete={onDelete}
                    />
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {hasAnnouncements && (
          <footer
            className={cn(
              'border-grey-300 bg-grey-150 shrink-0 border-t',
              PANEL_PADDING_X,
              'pt-4',
              PANEL_PADDING_BOTTOM
            )}
          >
            {role === 'admin' ? (
              <div className="flex gap-3">
                <Button
                  type="button"
                  variant="secondary"
                  className="flex-1"
                  onClick={onEditBoardClick}
                >
                  Edit Board
                </Button>
                <Button
                  type="button"
                  className="flex-1"
                  onClick={onCreateClick}
                >
                  Create Announcement
                </Button>
              </div>
            ) : (
              <Button type="button" className="w-full" onClick={onCreateClick}>
                Create Announcement
              </Button>
            )}
          </footer>
        )}
      </aside>
    </>
  );
}
