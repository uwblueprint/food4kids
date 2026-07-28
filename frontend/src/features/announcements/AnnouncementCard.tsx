import { useState } from 'react';

import EditIcon from '@/assets/icons/edit.svg?react';
import MoreVerticalIcon from '@/assets/icons/more-vertical.svg?react';
import TrashIcon from '@/assets/icons/trash.svg?react';
import { Button } from '@/common/components';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/common/components/Popover';
import { cn } from '@/lib/utils';
import type { Announcement } from '@/types/announcement';

import {
  announcementDateLine,
  authorColorClass,
  authorDisplayName,
  isAnnouncementEdited,
  isAnnouncementNew,
} from './utils';

interface AnnouncementCardProps {
  announcement: Announcement;
  currentUserId: string;
  canManage: boolean;
  onEdit: (announcement: Announcement) => void;
  onDelete: (announcement: Announcement) => void;
}

export function AnnouncementCard({
  announcement,
  currentUserId,
  canManage,
  onEdit,
  onDelete,
}: AnnouncementCardProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const isNew = isAnnouncementNew(announcement);
  const isEdited = isAnnouncementEdited(announcement);

  return (
    <article
      className={cn(
        'border-grey-300 bg-grey-100 relative flex flex-col gap-3 rounded-2xl border p-4',
        'shadow-card w-full transition-colors',
        canManage && 'hover:bg-grey-150'
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex min-w-0 flex-1 flex-col gap-1 text-left">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-h2 text-grey-500 font-bold">
              {announcement.subject}
            </h3>
            {isNew && (
              <span className="text-p3 rounded-full bg-blue-50 px-2 py-0.5 font-semibold text-blue-300">
                New
              </span>
            )}
            {isEdited && (
              <span className="text-p3 text-grey-400 font-semibold">
                Edited
              </span>
            )}
          </div>
          <p className="text-p2">
            <span
              className={cn(
                'font-medium',
                authorColorClass(announcement.author_role)
              )}
            >
              {authorDisplayName(announcement, currentUserId)}
            </span>
            <span className="text-grey-400">
              {' '}
              • {announcementDateLine(announcement)}
            </span>
          </p>
        </div>
        {canManage && (
          <Popover open={menuOpen} onOpenChange={setMenuOpen}>
            <PopoverTrigger asChild>
              <Button
                type="button"
                variant="ghost"
                shape="circular"
                className="size-9 shrink-0"
                aria-label="Announcement actions"
              >
                <MoreVerticalIcon className="text-grey-400 size-5" />
              </Button>
            </PopoverTrigger>
            <PopoverContent align="end" className="w-40 p-1">
              <button
                type="button"
                className="text-p2 text-grey-500 hover:bg-grey-200 flex w-full items-center gap-2 rounded-lg px-3 py-2"
                onClick={() => {
                  setMenuOpen(false);
                  onEdit(announcement);
                }}
              >
                <EditIcon className="size-4" />
                Edit
              </button>
              <button
                type="button"
                className="text-p2 text-red hover:bg-light-red flex w-full items-center gap-2 rounded-lg px-3 py-2"
                onClick={() => {
                  setMenuOpen(false);
                  onDelete(announcement);
                }}
              >
                <TrashIcon className="size-4" />
                Delete
              </button>
            </PopoverContent>
          </Popover>
        )}
      </div>
      <p className="text-p1 text-grey-500 line-clamp-4 w-full text-left whitespace-pre-wrap">
        {announcement.message}
      </p>
    </article>
  );
}
