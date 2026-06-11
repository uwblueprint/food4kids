import { useEffect, useState } from 'react';

import {
  Button,
  Field,
  FieldLabel,
  Input,
  Modal,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalTitle,
  Textarea,
} from '@/common/components';
import type { Announcement } from '@/types/announcement';

import { MESSAGE_MAX, SUBJECT_MAX } from './utils';

interface AnnouncementFormModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  mode: 'create' | 'edit';
  role: 'admin' | 'driver';
  announcement?: Announcement;
  onSubmit: (values: {
    subject: string;
    message: string;
    sendEmailToAll: boolean;
  }) => Promise<void>;
  isSubmitting?: boolean;
}

export function AnnouncementFormModal({
  open,
  onOpenChange,
  mode,
  role,
  announcement,
  onSubmit,
  isSubmitting = false,
}: AnnouncementFormModalProps) {
  const [subject, setSubject] = useState('');
  const [message, setMessage] = useState('');
  const [sendEmailToAll, setSendEmailToAll] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    if (mode === 'edit' && announcement) {
      setSubject(announcement.subject);
      setMessage(announcement.message);
    } else {
      setSubject('');
      setMessage('');
    }
    setSendEmailToAll(false);
    setError(null);
  }, [open, mode, announcement]);

  const trimmedSubject = subject.trim();
  const trimmedMessage = message.trim();
  const canSubmit = trimmedSubject.length > 0 && trimmedMessage.length > 0;

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!canSubmit) return;
    setError(null);
    try {
      await onSubmit({
        subject: trimmedSubject,
        message: trimmedMessage,
        sendEmailToAll,
      });
      onOpenChange(false);
    } catch (err) {
      const messageText =
        err instanceof Error
          ? err.message
          : 'Something went wrong. Please try again.';
      setError(messageText);
    }
  };

  return (
    <Modal open={open} onOpenChange={onOpenChange}>
      <ModalContent className="max-w-[560px]">
        <form onSubmit={handleSubmit} className="flex flex-col gap-6">
          <ModalHeader>
            <ModalTitle>Announcements</ModalTitle>
          </ModalHeader>

          <Field>
            <FieldLabel htmlFor="announcement-subject" required>
              Subject
            </FieldLabel>
            <Input
              id="announcement-subject"
              placeholder="Enter text here"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              maxCharacters={SUBJECT_MAX}
              characterCount={subject.length}
            />
          </Field>

          <Field>
            <FieldLabel htmlFor="announcement-message" required>
              Note
            </FieldLabel>
            <Textarea
              id="announcement-message"
              placeholder="Enter text here"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              maxCharacters={MESSAGE_MAX}
              characterCount={message.length}
            />
          </Field>

          {mode === 'create' && role === 'admin' && (
            <label className="text-p2 text-grey-500 flex cursor-pointer items-center gap-3">
              <input
                type="checkbox"
                className="border-grey-300 text-blue-300 size-4 rounded"
                checked={sendEmailToAll}
                onChange={(event) => setSendEmailToAll(event.target.checked)}
              />
              Send email to all
            </label>
          )}

          {error && (
            <p className="text-p2 text-red" role="alert">
              {error}
            </p>
          )}

          <ModalFooter>
            <Button
              type="button"
              variant="secondary"
              onClick={() => onOpenChange(false)}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting || !canSubmit}>
              {isSubmitting
                ? 'Saving…'
                : mode === 'create'
                  ? 'Post'
                  : 'Save'}
            </Button>
          </ModalFooter>
        </form>
      </ModalContent>
    </Modal>
  );
}
