import { useState } from 'react';

import type { NoteRead } from '@/api/generated/types.gen';
import EditIcon from '@/assets/icons/edit.svg?react';
import MoreHorizontalIcon from '@/assets/icons/more-horizontal.svg?react';
import TrashIcon from '@/assets/icons/trash.svg?react';
import { Button } from '@/common/components';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/common/components/Popover';

import { formatNoteDate, noteAuthorLabel } from './noteUtils';

interface NoteCardProps {
  note: NoteRead;
  currentUserId: string;
  currentUserName: string;
  canManage: boolean;
  onEdit: (note: NoteRead) => void;
  onDelete: (note: NoteRead) => void;
}

export function NoteCard({
  note,
  currentUserId,
  currentUserName,
  canManage,
  onEdit,
  onDelete,
}: NoteCardProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const attachments = note.attachments ?? [];
  const author = noteAuthorLabel(note, currentUserId, currentUserName);
  const date = formatNoteDate(note.created_at);

  return (
    <article className="border-grey-300 flex flex-col gap-2 rounded-xl border bg-white p-3">
      <div className="flex items-start justify-between gap-2">
        <p className="text-p2 text-grey-500 min-w-0">
          <span className="font-semibold">{author}</span>
          {date && <span className="text-grey-400"> • {date}</span>}
        </p>
        {canManage && (
          <Popover open={menuOpen} onOpenChange={setMenuOpen}>
            <PopoverTrigger asChild>
              <Button
                type="button"
                variant="ghost"
                shape="circular"
                className="size-8 shrink-0"
                aria-label="Note actions"
              >
                <MoreHorizontalIcon className="text-grey-400 size-5" />
              </Button>
            </PopoverTrigger>
            <PopoverContent align="end" className="w-40 p-1">
              <button
                type="button"
                className="text-p2 text-grey-500 hover:bg-grey-200 flex w-full items-center gap-2 rounded-sm px-3 py-2"
                onClick={() => {
                  setMenuOpen(false);
                  onEdit(note);
                }}
              >
                <EditIcon className="size-4" />
                Edit
              </button>
              <button
                type="button"
                className="text-p2 text-red hover:bg-light-red flex w-full items-center gap-2 rounded-sm px-3 py-2"
                onClick={() => {
                  setMenuOpen(false);
                  onDelete(note);
                }}
              >
                <TrashIcon className="size-4" />
                Delete
              </button>
            </PopoverContent>
          </Popover>
        )}
      </div>

      {attachments.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {attachments.map((attachment) => (
            <a
              key={attachment.filename}
              href={attachment.url}
              target="_blank"
              rel="noreferrer"
              className="border-grey-300 block size-16 overflow-hidden rounded-lg border"
            >
              <img
                src={attachment.url}
                alt=""
                className="size-full object-cover"
              />
            </a>
          ))}
        </div>
      )}

      <p className="text-p1 text-grey-500 whitespace-pre-wrap">
        {note.message}
      </p>
    </article>
  );
}
