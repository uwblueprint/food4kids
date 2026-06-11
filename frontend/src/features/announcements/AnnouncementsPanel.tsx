<<<<<<< HEAD
<<<<<<< HEAD
import { useCallback, useEffect, useRef, useState } from 'react';
=======
import { useEffect } from 'react';
>>>>>>> fa70cf5 (add board and crud functionality)
=======
import { useCallback, useEffect, useRef, useState } from 'react';
>>>>>>> b56351b (add bulk edit modal)

import RightPanelCloseIcon from '@/assets/icons/right-panel-close.svg?react';
import { Button, Spinner } from '@/common/components';
import { cn } from '@/lib/utils';
import type { Announcement } from '@/types/announcement';

import { AnnouncementCard } from './AnnouncementCard';
import { AnnouncementsEmptyState } from './AnnouncementsEmptyState';
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> b56351b (add bulk edit modal)
import {
  canManageAnnouncement,
  PANEL_CARD_GAP,
  PANEL_PADDING_BOTTOM,
  PANEL_PADDING_TOP,
  PANEL_PADDING_X,
  PANEL_SECTION_GAP,
  PANEL_WIDTH_DEFAULT,
  PANEL_WIDTH_MAX,
  PANEL_WIDTH_MIN,
} from './utils';
<<<<<<< HEAD
=======
import { canManageAnnouncement } from './utils';
>>>>>>> fa70cf5 (add board and crud functionality)
=======
>>>>>>> b56351b (add bulk edit modal)

interface AnnouncementsPanelProps {
  open: boolean;
  onClose: () => void;
  announcements: Announcement[];
  isLoading: boolean;
  currentUserId: string;
<<<<<<< HEAD
<<<<<<< HEAD
  readIds: Set<string>;
  role: 'admin' | 'driver';
  panelWidth: number;
  onPanelWidthChange: (width: number) => void;
  onCreateClick: () => void;
  onEditBoardClick: () => void;
  onAnnouncementOpen: (announcement: Announcement) => void;
=======
=======
  readIds: Set<string>;
>>>>>>> b56351b (add bulk edit modal)
  role: 'admin' | 'driver';
  panelWidth: number;
  onPanelWidthChange: (width: number) => void;
  onCreateClick: () => void;
<<<<<<< HEAD
>>>>>>> fa70cf5 (add board and crud functionality)
=======
  onEditBoardClick: () => void;
  onAnnouncementOpen: (announcement: Announcement) => void;
>>>>>>> b56351b (add bulk edit modal)
  onEdit: (announcement: Announcement) => void;
  onDelete: (announcement: Announcement) => void;
}

export function AnnouncementsPanel({
  open,
  onClose,
  announcements,
  isLoading,
  currentUserId,
<<<<<<< HEAD
<<<<<<< HEAD
  readIds,
  role,
  panelWidth,
  onPanelWidthChange,
  onCreateClick,
  onEditBoardClick,
  onAnnouncementOpen,
  onEdit,
  onDelete,
}: AnnouncementsPanelProps) {
  const resizeRef = useRef<{ startX: number; startWidth: number } | null>(null);
  const [isResizing, setIsResizing] = useState(false);

=======
=======
  readIds,
>>>>>>> b56351b (add bulk edit modal)
  role,
  panelWidth,
  onPanelWidthChange,
  onCreateClick,
  onEditBoardClick,
  onAnnouncementOpen,
  onEdit,
  onDelete,
}: AnnouncementsPanelProps) {
<<<<<<< HEAD
>>>>>>> fa70cf5 (add board and crud functionality)
=======
  const resizeRef = useRef<{ startX: number; startWidth: number } | null>(null);
  const [isResizing, setIsResizing] = useState(false);

>>>>>>> b56351b (add bulk edit modal)
  useEffect(() => {
    if (!open) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [open, onClose]);

<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> b56351b (add bulk edit modal)
  const handleResizeMove = useCallback(
    (event: MouseEvent) => {
      if (!resizeRef.current) return;
      const delta = resizeRef.current.startX - event.clientX;
      const next = Math.min(
        PANEL_WIDTH_MAX,
        Math.max(PANEL_WIDTH_MIN, resizeRef.current.startWidth + delta)
      );
      onPanelWidthChange(next);
    },
    [onPanelWidthChange]
  );

  const handleResizeEnd = useCallback(() => {
    resizeRef.current = null;
    setIsResizing(false);
    document.body.style.cursor = '';
    document.body.style.userSelect = '';
    window.removeEventListener('mousemove', handleResizeMove);
    window.removeEventListener('mouseup', handleResizeEnd);
  }, [handleResizeMove]);

  const handleResizeStart = (event: React.MouseEvent) => {
    event.preventDefault();
    resizeRef.current = { startX: event.clientX, startWidth: panelWidth };
    setIsResizing(true);
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
    window.addEventListener('mousemove', handleResizeMove);
    window.addEventListener('mouseup', handleResizeEnd);
  };

  useEffect(() => {
    return () => {
      window.removeEventListener('mousemove', handleResizeMove);
      window.removeEventListener('mouseup', handleResizeEnd);
    };
  }, [handleResizeMove, handleResizeEnd]);

  if (!open) return null;

  const hasAnnouncements = announcements.length > 0;

<<<<<<< HEAD
=======
  if (!open) return null;

>>>>>>> fa70cf5 (add board and crud functionality)
=======
>>>>>>> b56351b (add bulk edit modal)
  return (
    <>
      <button
        type="button"
        aria-label="Close announcements"
        className="fixed inset-0 z-40 bg-black/40 md:bg-black/30"
        onClick={onClose}
      />
      <aside
<<<<<<< HEAD
<<<<<<< HEAD
        style={{ '--panel-w': `${panelWidth}px` } as React.CSSProperties}
        className={cn(
          'bg-grey-100 fixed z-50 flex h-full flex-col shadow-harsh',
          'inset-0 w-full md:inset-y-0 md:right-0 md:left-auto md:w-[var(--panel-w)]',
          'md:rounded-l-2xl',
          isResizing && 'select-none'
=======
        className={cn(
          'bg-grey-100 fixed z-50 flex flex-col shadow-harsh',
          'inset-0 md:inset-y-0 md:right-0 md:left-auto md:w-full md:max-w-[420px]',
          'md:rounded-l-2xl'
>>>>>>> fa70cf5 (add board and crud functionality)
=======
        style={{ '--panel-w': `${panelWidth}px` } as React.CSSProperties}
        className={cn(
          'bg-grey-100 fixed z-50 flex h-full flex-col shadow-harsh',
          'inset-0 w-full md:inset-y-0 md:right-0 md:left-auto md:w-[var(--panel-w)]',
          'md:rounded-l-2xl',
          isResizing && 'select-none'
>>>>>>> b56351b (add bulk edit modal)
        )}
        role="dialog"
        aria-modal="true"
        aria-labelledby="announcements-panel-title"
      >
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> b56351b (add bulk edit modal)
        <div
          role="separator"
          aria-orientation="vertical"
          aria-label="Resize announcements panel"
          className="absolute top-0 left-0 hidden h-full w-2 cursor-col-resize md:block"
          onMouseDown={handleResizeStart}
        />

        <header
          className={cn(
            'border-grey-300 flex shrink-0 items-center justify-between border-b',
            PANEL_PADDING_X,
            PANEL_PADDING_TOP,
            'pb-4'
          )}
        >
<<<<<<< HEAD
=======
        <header className="border-grey-300 flex shrink-0 items-center justify-between border-b px-5 py-4 md:px-6">
>>>>>>> fa70cf5 (add board and crud functionality)
=======
>>>>>>> b56351b (add bulk edit modal)
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
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> b56351b (add bulk edit modal)
            <div
              className={cn(
                'flex flex-1 items-center justify-center',
                PANEL_PADDING_X,
                PANEL_SECTION_GAP
              )}
            >
<<<<<<< HEAD
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
                        currentUserId
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
              'border-grey-300 shadow-card shrink-0 border-t',
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
=======
            <div className="flex flex-1 items-center justify-center py-16">
=======
>>>>>>> b56351b (add bulk edit modal)
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
                        currentUserId
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

<<<<<<< HEAD
        {announcements.length > 0 && (
          <footer className="border-grey-300 shrink-0 border-t p-5 md:p-6">
            <Button
              type="button"
              className="w-full"
              onClick={onCreateClick}
            >
              Create Announcement
            </Button>
>>>>>>> fa70cf5 (add board and crud functionality)
=======
        {hasAnnouncements && (
          <footer
            className={cn(
              'border-grey-300 shadow-card shrink-0 border-t',
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
>>>>>>> b56351b (add bulk edit modal)
          </footer>
        )}
      </aside>
    </>
  );
}
<<<<<<< HEAD
<<<<<<< HEAD

export { PANEL_WIDTH_DEFAULT };
=======
>>>>>>> fa70cf5 (add board and crud functionality)
=======

export { PANEL_WIDTH_DEFAULT };
>>>>>>> b56351b (add bulk edit modal)
