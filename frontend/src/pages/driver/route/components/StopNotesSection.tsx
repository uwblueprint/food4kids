import { useState } from 'react';

import { useAuthStore } from '@/api/authStore';
import { describeApiFailure } from '@/api/errors';
import type { Attachment, NoteRead } from '@/api/generated/types.gen';
import {
  useCreateNote,
  useDeleteNote,
  useNotes,
  useUpdateNote,
} from '@/api/notes';
import { Button, Spinner } from '@/common/components';
import { cn } from '@/lib/utils';

import { NoteCard } from './NoteCard';
import { NoteDeleteConfirmModal } from './NoteDeleteConfirmModal';
import { NoteFormModal } from './NoteFormModal';
import { canManageNote } from './noteUtils';

interface StopNotesSectionProps {
  noteChainId: string | null | undefined;
  enabled: boolean;
}

export function StopNotesSection({
  noteChainId,
  enabled,
}: StopNotesSectionProps) {
  const currentUserId = useAuthStore((state) => state.user?.id ?? '');
  const role = useAuthStore((state) => state.user?.role ?? 'driver');

  const {
    data: notes = [],
    isLoading,
    isError,
  } = useNotes(noteChainId, enabled && !!noteChainId);

  const createNote = useCreateNote(noteChainId ?? '');
  const updateNote = useUpdateNote(noteChainId ?? '');
  const deleteNote = useDeleteNote(noteChainId ?? '');

  const [formOpen, setFormOpen] = useState(false);
  const [formMode, setFormMode] = useState<'create' | 'edit'>('create');
  const [editingNote, setEditingNote] = useState<NoteRead | undefined>();
  const [noteToDelete, setNoteToDelete] = useState<NoteRead | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const openCreate = () => {
    setFormMode('create');
    setEditingNote(undefined);
    setFormOpen(true);
  };

  const openEdit = (note: NoteRead) => {
    setFormMode('edit');
    setEditingNote(note);
    setFormOpen(true);
  };

  const openDelete = (note: NoteRead) => {
    setDeleteError(null);
    setNoteToDelete(note);
  };

  const handleSubmit = async ({
    message,
    attachments,
  }: {
    message: string;
    attachments: Attachment[];
  }) => {
    if (!noteChainId) return;

    if (formMode === 'edit' && editingNote) {
      await updateNote.mutateAsync({
        path: {
          note_chain_id: noteChainId,
          note_id: editingNote.note_id,
        },
        body: { message },
      });
      return;
    }

    await createNote.mutateAsync({
      path: { note_chain_id: noteChainId },
      body: { message, attachments },
    });
  };

  const handleDelete = async () => {
    if (!noteChainId || !noteToDelete) return;
    setDeleteError(null);
    try {
      await deleteNote.mutateAsync({
        path: {
          note_chain_id: noteChainId,
          note_id: noteToDelete.note_id,
        },
      });
      setNoteToDelete(null);
    } catch (err) {
      setDeleteError(
        describeApiFailure(err) ??
          (err instanceof Error
            ? err.message
            : 'Couldn’t delete this note. Please try again.')
      );
    }
  };

  if (!noteChainId) {
    return (
      <section className="flex flex-col gap-3">
        <h3 className="text-h3 font-nunito-sans text-grey-500 font-bold">
          Notes
        </h3>
        <p className="text-p2 text-grey-400">
          Notes are not available for this stop.
        </p>
      </section>
    );
  }

  return (
    <section className="flex flex-col gap-3">
      <h3 className="text-h3 font-nunito-sans text-grey-500 font-bold">
        Notes
      </h3>

      {isLoading && (
        <div className="flex justify-center py-4">
          <Spinner />
        </div>
      )}

      {isError && (
        <p className="text-p2 text-red" role="alert">
          Couldn&apos;t load notes. Please try again.
        </p>
      )}

      {!isLoading && !isError && notes.length === 0 && (
        <p className="text-p2 text-grey-400">No notes yet.</p>
      )}

      {/* One card holds the whole thread plus the compose button, with the
          notes hairline-separated inside it. The notes are one conversation
          about this stop, not a stack of unrelated cards. With no notes there
          is no thread to hold, and the card collapses to a white ring around
          the button. */}
      {!isLoading && (
        <div
          className={cn(
            'flex flex-col',
            notes.length > 0 && 'rounded-xl bg-white p-2'
          )}
        >
          {notes.map((note, index) => (
            <div
              key={note.note_id}
              className={index > 0 ? 'border-grey-200 border-t' : undefined}
            >
              <NoteCard
                note={note}
                currentUserId={currentUserId}
                canManage={canManageNote(note, currentUserId, role)}
                onEdit={openEdit}
                onDelete={openDelete}
              />
            </div>
          ))}

          <Button type="button" className="w-full" onClick={openCreate}>
            Add note
          </Button>
        </div>
      )}

      <NoteFormModal
        open={formOpen}
        onOpenChange={setFormOpen}
        mode={formMode}
        note={editingNote}
        onSubmit={handleSubmit}
        isSubmitting={createNote.isPending || updateNote.isPending}
      />

      <NoteDeleteConfirmModal
        open={!!noteToDelete}
        onOpenChange={(open) => {
          if (!open) {
            setNoteToDelete(null);
            setDeleteError(null);
          }
        }}
        onConfirm={() => {
          void handleDelete();
        }}
        isLoading={deleteNote.isPending}
        error={deleteError}
      />
    </section>
  );
}
