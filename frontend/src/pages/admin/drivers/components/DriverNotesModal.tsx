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
  ModalFooter,
  ModalHeader,
  ModalTitle,
  Textarea,
} from '@/common/components';

interface DriverNotesModalProps {
  noteChainId: string;
  notes: NoteRead[];
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function DriverNotesModal({
  noteChainId,
  notes,
  open,
  onOpenChange,
}: DriverNotesModalProps) {
  const create = useCreateNote(noteChainId);
  const remove = useDeleteNote(noteChainId);
  const [message, setMessage] = useState('');

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
      <ModalContent className="max-w-[560px]">
        <ModalHeader>
          <ModalTitle variant="confirmation">Edit Driver Notes</ModalTitle>
        </ModalHeader>
        <div className="divide-grey-200 divide-y">
          {notes.map((note) => (
            <div key={note.note_id} className="flex items-start gap-3 py-3">
              <p className="text-p2 text-grey-500 flex-1">{note.message}</p>
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
                className="text-grey-400 hover:text-red"
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
          <Button variant="primary" onClick={() => void save()} disabled={create.isPending}>
            Save
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}
