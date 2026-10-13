import { useState } from 'react';

import type { RoleEnum } from '@/api/generated/types.gen';
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
import { cn } from '@/lib/utils';
import type { Announcement } from '@/types/announcement';

import {
  DESKTOP_MODAL_LAYOUT,
  MESSAGE_MAX,
  SHEET_MODAL_LAYOUT,
  sheetHeightStyle,
  SUBJECT_MAX,
} from './utils';

const EMAIL_GROUP_LABEL_ID = 'announcement-email-audiences';

interface AnnouncementFormModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  mode: 'create' | 'edit';
  role: 'admin' | 'driver';
  announcement?: Announcement;
  onSubmit: (values: {
    subject: string;
    message: string;
    emailAudiences: RoleEnum[];
  }) => Promise<void>;
  isSubmitting?: boolean;
}

interface AnnouncementFormProps {
  mode: 'create' | 'edit';
  role: 'admin' | 'driver';
  announcement?: Announcement;
  onSubmit: AnnouncementFormModalProps['onSubmit'];
  onOpenChange: (open: boolean) => void;
  isSubmitting: boolean;
}

function AnnouncementForm({
  mode,
  role,
  announcement,
  onSubmit,
  onOpenChange,
  isSubmitting,
}: AnnouncementFormProps) {
  const [subject, setSubject] = useState(() =>
    mode === 'edit' && announcement ? announcement.subject : ''
  );
  const [message, setMessage] = useState(() =>
    mode === 'edit' && announcement ? announcement.message : ''
  );
  const [emailAdmins, setEmailAdmins] = useState(false);
  const [emailDrivers, setEmailDrivers] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const emailAudienceOptions = [
    {
      label: 'Admins',
      checked: emailAdmins,
      onChange: setEmailAdmins,
    },
    {
      label: 'Drivers',
      checked: emailDrivers,
      onChange: setEmailDrivers,
    },
  ];

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
        emailAudiences: [
          ...(emailAdmins ? (['admin'] as const) : []),
          ...(emailDrivers ? (['driver'] as const) : []),
        ],
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
    <form
      onSubmit={handleSubmit}
      className="flex min-h-0 flex-1 flex-col gap-6"
    >
      <ModalHeader className="shrink-0">
        <ModalTitle variant="form">Announcements</ModalTitle>
      </ModalHeader>

      <Field className="shrink-0">
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

      <Field className="flex min-h-0 flex-1 flex-col overflow-hidden">
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
          className="min-h-0 resize-none"
          wrapperClassName="flex-1"
        />
      </Field>

      {mode === 'create' && role === 'admin' && (
        /* Labelled like the fields above so it reads as part of the form
         * rather than a stray pair of boxes. role="group" + aria-labelledby
         * rather than a fieldset/legend, which does not lay out as flex. */
        <div
          role="group"
          aria-labelledby={EMAIL_GROUP_LABEL_ID}
          className="flex shrink-0 flex-col gap-2"
        >
          <span
            id={EMAIL_GROUP_LABEL_ID}
            className="text-h3 text-grey-500 font-bold"
          >
            Send email to
          </span>
          <div className="flex flex-wrap items-center gap-x-8 gap-y-2">
            {emailAudienceOptions.map(({ label, checked, onChange }) => (
              <label
                key={label}
                className="text-p2 text-grey-500 flex cursor-pointer items-center gap-3"
              >
                <input
                  type="checkbox"
                  className="border-grey-300 size-4 rounded text-blue-300"
                  checked={checked}
                  onChange={(event) => onChange(event.target.checked)}
                />
                {label}
              </label>
            ))}
          </div>
        </div>
      )}

      {error && (
        <p className="text-p2 text-red" role="alert">
          {error}
        </p>
      )}

      <ModalFooter className="mt-auto shrink-0 [&_button]:flex-1">
        <Button
          type="button"
          variant="secondary"
          onClick={() => onOpenChange(false)}
          disabled={isSubmitting}
        >
          Cancel
        </Button>
        <Button type="submit" disabled={isSubmitting || !canSubmit}>
          {isSubmitting ? 'Saving…' : mode === 'create' ? 'Post' : 'Save'}
        </Button>
      </ModalFooter>
    </form>
  );
}

function formKey(mode: 'create' | 'edit', announcement?: Announcement): string {
  if (mode === 'edit' && announcement) {
    return `edit-${announcement.announcement_id}`;
  }
  return 'create';
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
          <AnnouncementForm
            key={formKey(mode, announcement)}
            mode={mode}
            role={role}
            announcement={announcement}
            onSubmit={onSubmit}
            onOpenChange={onOpenChange}
            isSubmitting={isSubmitting}
          />
        ) : null}
      </ModalContent>
    </Modal>
  );
}
