import { type FormEvent, useState } from 'react';

import { useInitializeDriver } from '@/api/drivers';
import CheckIcon from '@/assets/icons/check.svg?react';
import {
  Button,
  Field,
  FieldLabel,
  Input,
  Modal,
  ModalContent,
  ModalDescription,
  ModalFooter,
  ModalHeader,
  ModalTitle,
} from '@/common/components';

interface AddDriverModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function AddDriverModal({ open, onOpenChange }: AddDriverModalProps) {
  const initialize = useInitializeDriver();
  const [sent, setSent] = useState(false);
  const [emailError, setEmailError] = useState('');

  const handleOpenChange = (next: boolean) => {
    if (!next) {
      setSent(false);
      setEmailError('');
      initialize.reset();
    }
    onOpenChange(next);
  };

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    setEmailError('');
    initialize.mutate(
      {
        body: {
          first_name: String(data.get('first_name') ?? '').trim(),
          last_name: String(data.get('last_name') ?? '').trim(),
          email: String(data.get('email') ?? '').trim(),
          phone: String(data.get('phone') ?? '').trim() || null,
        },
      },
      {
        onSuccess: () => setSent(true),
        onError: () =>
          setEmailError('A driver with this email already exists.'),
      }
    );
  };

  return (
    <Modal open={open} onOpenChange={handleOpenChange}>
      <ModalContent className="max-w-[520px] bg-white" showCloseButton={false}>
        {sent ? (
          <div className="flex flex-col items-center gap-5 py-5 text-center">
            <span className="flex size-12 items-center justify-center rounded-full bg-blue-50 text-blue-300">
              <CheckIcon className="size-6" />
            </span>
            <div>
              <ModalTitle variant="confirmation">Invite sent</ModalTitle>
              <p className="text-p2 text-grey-400 mt-2">
                The driver will receive an email to set up their account.
              </p>
            </div>
            <Button variant="primary" onClick={() => handleOpenChange(false)}>
              Done
            </Button>
          </div>
        ) : (
          <form onSubmit={submit} className="flex flex-col gap-4">
            <ModalHeader>
              <ModalTitle variant="confirmation">Add Driver</ModalTitle>
              <ModalDescription>
                They&apos;ll get an email to set up their account
              </ModalDescription>
            </ModalHeader>
            <Field>
              <FieldLabel required>First Name</FieldLabel>
              <Input
                name="first_name"
                placeholder="Enter first name"
                required
              />
            </Field>
            <Field>
              <FieldLabel required>Last Name</FieldLabel>
              <Input name="last_name" placeholder="Enter last name" required />
            </Field>
            <Field>
              <FieldLabel required>Email</FieldLabel>
              <Input
                name="email"
                type="email"
                placeholder="name@example.com"
                required
                error={emailError}
              />
            </Field>
            <Field>
              <FieldLabel>Phone Number</FieldLabel>
              <Input name="phone" type="tel" placeholder="(555) 555-5555" />
            </Field>
            <ModalFooter className="pt-2">
              <Button
                type="button"
                variant="tertiary"
                onClick={() => handleOpenChange(false)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                disabled={initialize.isPending}
              >
                Send invite
              </Button>
            </ModalFooter>
          </form>
        )}
      </ModalContent>
    </Modal>
  );
}
