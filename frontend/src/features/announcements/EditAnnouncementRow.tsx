import TrashIcon from '@/assets/icons/trash.svg?react';
import UndoIcon from '@/assets/icons/undo.svg?react';
import { Button } from '@/common/components';
import { cn } from '@/lib/utils';
import type { Announcement } from '@/types/announcement';

import {
  announcementDateLine,
  authorColorClass,
  authorDisplayName,
} from './utils';

interface EditAnnouncementRowProps {
  announcement: Announcement;
  currentUserId: string;
  pendingDelete: boolean;
  onToggleDelete: (announcement: Announcement) => void;
}

export function EditAnnouncementRow({
  announcement,
  currentUserId,
  pendingDelete,
  onToggleDelete,
}: EditAnnouncementRowProps) {
  const deletedTextClass = pendingDelete
    ? 'text-grey-400 line-through decoration-grey-400'
    : undefined;

  return (
    <article className="flex items-start gap-4">
      <div className="flex min-w-0 flex-1 flex-col gap-1">
        <h3
          className={cn(
            'text-h2 font-bold',
            pendingDelete ? deletedTextClass : 'text-grey-500'
          )}
        >
          {announcement.subject}
        </h3>
        <p className={cn('text-p2', pendingDelete && deletedTextClass)}>
          <span
            className={cn(
              'font-medium',
              pendingDelete
                ? deletedTextClass
                : authorColorClass(announcement.author_role)
            )}
          >
            {authorDisplayName(announcement, currentUserId)}
          </span>
          <span
            className={cn(pendingDelete ? deletedTextClass : 'text-grey-400')}
          >
            {' '}
            • {announcementDateLine(announcement)}
          </span>
        </p>
        <p
          className={cn(
            'text-p1 line-clamp-2 whitespace-pre-wrap',
            pendingDelete ? deletedTextClass : 'text-grey-500'
          )}
        >
          {announcement.message}
        </p>
      </div>

      <Button
        type="button"
        variant="secondary"
        shape="circular"
        className="shrink-0"
        aria-label={
          pendingDelete
            ? `Undo delete ${announcement.subject}`
            : `Delete ${announcement.subject}`
        }
        onClick={() => onToggleDelete(announcement)}
      >
        {pendingDelete ? (
          <UndoIcon className="text-grey-500 size-5" />
        ) : (
          <TrashIcon className="text-grey-400 size-5" />
        )}
      </Button>
    </article>
  );
}
