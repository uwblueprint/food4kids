import { useState } from 'react';

import type { NoteRead } from '@/api/generated/types.gen';
import { useCreateNote, useDeleteNote } from '@/api/notes';
import TrashIcon from '@/assets/icons/trash.svg?react';
import {
  Button,
  Field,
  FieldLabel,
  Modal,
  ModalContent,
  ModalDescription,
  ModalFooter,
  ModalHeader,
  ModalTitle,
  Textarea,
} from '@/common/components';

interface DriverNotesModalProps {
  driverName: string;
  noteChainId: string;
  notes: NoteRead[];
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function DriverNotesModal({
  driverName,
  noteChainId,
  notes,
  open,
  onOpenChange,
}: DriverNotesModalProps) {
  const create = useCreateNote(noteChainId);
  const remove = useDeleteNote(noteChainId);
  const [message, setMessage] = useState('');

  const formatTimestamp = (value: string | null | undefined) => {
    if (!value) return '';
    return new Date(value).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    });
  };

  const save = async () => {
    if (message.trim()) {
      await create.mutateAsync({
        path: { note_chain_id: noteChainId },
        body: { message: message.trim(), attachments: [] },
      });
    }
    setMessage('');
    onOpenChange(false);
  };

  return (
    <Modal open={open} onOpenChange={onOpenChange}>
      <ModalContent className="max-w-[560px] bg-white">
        <ModalHeader>
          <ModalTitle variant="confirmation">Edit Driver Notes</ModalTitle>
          <ModalDescription>Edit the notes of {driverName}</ModalDescription>
        </ModalHeader>
        <div className="flex flex-col gap-3">
          {notes.map((note) => (
            <div
              key={note.note_id}
              className="border-grey-200 flex items-start gap-3 rounded-lg border p-3"
            >
              <div className="flex-1">
                <p className="text-p2 text-grey-500">{note.message}</p>
                <p className="text-p3 text-grey-400 mt-1">
                  {formatTimestamp(note.created_at)}
                </p>
              </div>
              <button
                type="button"
                aria-label="Delete note"
                onClick={() =>
                  remove.mutate({
                    path: {
                      note_chain_id: noteChainId,
                      note_id: note.note_id,
                    },
                  })
                }
                className="border-grey-300 text-grey-400 hover:text-red flex size-8 shrink-0 items-center justify-center rounded-full border"
              >
                <TrashIcon className="size-4" />
              </button>
            </div>
          ))}
        </div>
        <Field>
          <FieldLabel>New Note</FieldLabel>
          <Textarea
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            placeholder="Enter text here"
          />
        </Field>
        <ModalFooter className="pt-2">
          <Button variant="tertiary" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={() => void save()}
            disabled={create.isPending}
          >
            Save
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}
