import { useEffect, useRef, useState } from 'react';

import { describeApiFailure } from '@/api/errors';
import type { Attachment, NoteRead } from '@/api/generated/types.gen';
import { useUploadImage } from '@/api/notes';
import XIcon from '@/assets/icons/x.svg?react';
import {
  Button,
  Field,
  FieldLabel,
  Modal,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalTitle,
} from '@/common/components';
import {
  DESKTOP_MODAL_LAYOUT,
  SHEET_MODAL_LAYOUT,
  sheetHeightStyle,
} from '@/features/announcements/utils';
import { cn } from '@/lib/utils';

import {
  isAllowedNoteImage,
  NOTE_IMAGE_ACCEPT,
  NOTE_IMAGE_MAX,
  NOTE_IMAGE_MAX_BYTES,
  NOTE_MESSAGE_MAX,
} from './noteUtils';

interface PendingImage {
  previewUrl: string;
  file: File;
}

interface NoteFormModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  mode: 'create' | 'edit';
  note?: NoteRead;
  onSubmit: (values: {
    message: string;
    attachments: Attachment[];
  }) => Promise<void>;
  isSubmitting?: boolean;
}

function formKey(mode: 'create' | 'edit', note?: NoteRead): string {
  if (mode === 'edit' && note) return `edit-${note.note_id}`;
  return 'create';
}

function RemoveImageButton({
  disabled,
  onClick,
}: {
  disabled?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      className="bg-grey-400 text-grey-100 hover:bg-grey-500 absolute -top-1.5 -right-1.5 flex size-5 items-center justify-center rounded-full transition-colors disabled:opacity-60"
      aria-label="Remove image"
      disabled={disabled}
      onClick={onClick}
    >
      <XIcon className="size-3" />
    </button>
  );
}

function NoteForm({
  mode,
  note,
  onSubmit,
  onOpenChange,
  isSubmitting,
}: {
  mode: 'create' | 'edit';
  note?: NoteRead;
  onSubmit: NoteFormModalProps['onSubmit'];
  onOpenChange: (open: boolean) => void;
  isSubmitting: boolean;
}) {
  const [message, setMessage] = useState(() =>
    mode === 'edit' && note ? note.message : ''
  );
  const [images, setImages] = useState<PendingImage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const imagesRef = useRef(images);
  const uploadImage = useUploadImage();

  useEffect(() => {
    imagesRef.current = images;
  }, [images]);

  useEffect(() => {
    return () => {
      for (const image of imagesRef.current) {
        URL.revokeObjectURL(image.previewUrl);
      }
    };
  }, []);

  const trimmed = message.trim();
  const busy = isSubmitting || isSaving;
  const canSubmit =
    trimmed.length > 0 && trimmed.length <= NOTE_MESSAGE_MAX && !busy;
  const isOverCharThreshold = message.length >= NOTE_MESSAGE_MAX * 0.8;

  const handleFilesSelected = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files ?? []);
    event.target.value = '';
    if (files.length === 0) return;

    const remaining = NOTE_IMAGE_MAX - images.length;
    if (remaining <= 0) {
      setError(`You can attach up to ${NOTE_IMAGE_MAX} images.`);
      return;
    }

    const staged: PendingImage[] = [];
    for (const file of files.slice(0, remaining)) {
      if (!isAllowedNoteImage(file)) {
        setError('Images must be PNG, JPEG, or GIF.');
        continue;
      }
      if (file.size > NOTE_IMAGE_MAX_BYTES) {
        setError('Each image must be 5 MB or smaller.');
        continue;
      }
      staged.push({
        previewUrl: URL.createObjectURL(file),
        file,
      });
    }

    if (staged.length === 0) return;
    setError(null);
    setImages((current) => [...current, ...staged]);
  };

  const removeImage = (previewUrl: string) => {
    setImages((current) => {
      const target = current.find((image) => image.previewUrl === previewUrl);
      if (target) URL.revokeObjectURL(target.previewUrl);
      return current.filter((image) => image.previewUrl !== previewUrl);
    });
  };

  const uploadStagedImages = async (): Promise<Attachment[]> => {
    const attachments: Attachment[] = [];
    for (const image of images) {
      const data = await uploadImage.mutateAsync({
        body: { file: image.file },
      });
      const url = data['url'];
      const filename = data['filename'];
      if (!url || !filename) {
        throw new Error('Upload response was missing url or filename.');
      }
      attachments.push({ url, filename });
    }
    return attachments;
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!canSubmit) return;
    setError(null);
    setIsSaving(true);
    try {
      const attachments =
        mode === 'create' && images.length > 0
          ? await uploadStagedImages()
          : [];
      await onSubmit({ message: trimmed, attachments });
      onOpenChange(false);
    } catch (err) {
      setError(
        describeApiFailure(err) ??
          (err instanceof Error
            ? err.message
            : 'Something went wrong. Please try again.')
      );
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="flex min-h-0 flex-1 flex-col gap-6"
    >
      <ModalHeader className="shrink-0">
        <ModalTitle variant="form">
          {mode === 'edit' ? 'Edit note' : 'Announcements'}
        </ModalTitle>
      </ModalHeader>

      <Field className="flex min-h-0 flex-1 flex-col">
        <FieldLabel htmlFor="stop-note-message">Note</FieldLabel>

        <div className="flex min-h-0 flex-1 flex-col gap-2">
          <div
            className={cn(
              'border-grey-300 flex min-h-0 flex-1 flex-col rounded-xl border bg-white',
              'focus-within:border-blue-300 focus-within:ring-1 focus-within:ring-blue-300',
              busy && 'bg-grey-150 cursor-not-allowed opacity-60',
              error &&
                'border-red focus-within:border-red focus-within:ring-red'
            )}
          >
            <textarea
              id="stop-note-message"
              placeholder="Enter text here"
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              maxLength={NOTE_MESSAGE_MAX}
              disabled={busy}
              className={cn(
                'text-m-p2 text-grey-500 font-normal',
                'placeholder:text-[length:var(--text-p2)]',
                'placeholder:leading-[var(--text-p2--line-height)]',
                'placeholder:text-grey-400 placeholder:font-semibold',
                'box-border min-h-[160px] w-full flex-1 resize-none bg-transparent px-3 py-3 outline-none',
                'disabled:text-grey-400 disabled:cursor-not-allowed'
              )}
            />

            {mode === 'create' && images.length > 0 && (
              <div className="flex flex-wrap gap-2 px-3 pt-2 pr-4 pb-3">
                {images.map((image) => (
                  <div
                    key={image.previewUrl}
                    className="relative size-16 shrink-0"
                  >
                    <div className="border-grey-300 size-full overflow-hidden rounded-lg border">
                      <img
                        src={image.previewUrl}
                        alt=""
                        className="size-full object-cover"
                      />
                    </div>
                    <RemoveImageButton
                      disabled={busy}
                      onClick={() => removeImage(image.previewUrl)}
                    />
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="text-p3 text-grey-400 flex flex-col items-end gap-0.5">
            <p
              className={cn(isOverCharThreshold ? 'text-red' : 'text-grey-400')}
            >
              {message.length}/{NOTE_MESSAGE_MAX} characters
            </p>
            {mode === 'create' && (
              <p>
                {images.length}/{NOTE_IMAGE_MAX} images
              </p>
            )}
          </div>
        </div>
      </Field>

      {error && (
        <p className="text-p2 text-red" role="alert">
          {error}
        </p>
      )}

      <ModalFooter className="tablet:flex-row tablet:[&_button]:flex-1 mt-auto shrink-0 flex-col [&_button]:w-full">
        {mode === 'create' && (
          <>
            <input
              ref={fileInputRef}
              type="file"
              accept={NOTE_IMAGE_ACCEPT}
              multiple
              className="hidden"
              onChange={handleFilesSelected}
            />
            <Button
              type="button"
              variant="secondary"
              disabled={busy || images.length >= NOTE_IMAGE_MAX}
              onClick={() => fileInputRef.current?.click()}
            >
              Upload image
            </Button>
          </>
        )}
        <Button type="submit" disabled={!canSubmit}>
          {busy ? 'Saving…' : mode === 'edit' ? 'Save' : 'Add note'}
        </Button>
      </ModalFooter>
    </form>
  );
}

export function NoteFormModal({
  open,
  onOpenChange,
  mode,
  note,
  onSubmit,
  isSubmitting = false,
}: NoteFormModalProps) {
  return (
    <Modal open={open} onOpenChange={onOpenChange}>
      <ModalContent
        className={cn(
          'flex min-h-0 flex-col',
          SHEET_MODAL_LAYOUT,
          DESKTOP_MODAL_LAYOUT,
          'desktop:h-[min(560px,85vh)]'
        )}
        style={sheetHeightStyle() as React.CSSProperties}
      >
        {open ? (
          <NoteForm
            key={formKey(mode, note)}
            mode={mode}
            note={note}
            onSubmit={onSubmit}
            onOpenChange={onOpenChange}
            isSubmitting={isSubmitting}
          />
        ) : null}
      </ModalContent>
    </Modal>
  );
}
