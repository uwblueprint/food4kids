import { Dialog as DialogPrimitive } from 'radix-ui';
import * as React from 'react';

import XIcon from '@/assets/icons/x.svg?react';
import { cn } from '@/lib/utils';

const Modal = DialogPrimitive.Root;
const ModalTrigger = DialogPrimitive.Trigger;
const ModalPortal = DialogPrimitive.Portal;
const ModalClose = DialogPrimitive.Close;

function ModalOverlay({
  className,
  ...props
}: React.ComponentProps<typeof DialogPrimitive.Overlay>) {
  return (
    <DialogPrimitive.Overlay
      className={cn(
        'fixed inset-0 z-50 bg-black/40',
        'data-[state=open]:animate-in data-[state=closed]:animate-out',
        'data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0',
        className
      )}
      {...props}
    />
  );
}

function ModalContent({
  className,
  children,
  showCloseButton = true,
  ...props
}: React.ComponentProps<typeof DialogPrimitive.Content> & {
  showCloseButton?: boolean;
}) {
  return (
    <ModalPortal>
      <ModalOverlay />
      <DialogPrimitive.Content
        aria-describedby={undefined}
        className={cn(
          'fixed top-1/2 left-1/2 z-50 w-full max-w-[600px] -translate-x-1/2 -translate-y-1/2',
          'bg-grey-100 shadow-harsh rounded-xl p-6',
          'flex flex-col items-stretch gap-4',
          'data-[state=open]:animate-in data-[state=closed]:animate-out',
          'data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0',
          'data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95',
          className
        )}
        {...props}
      >
        {children}
        {showCloseButton && (
          <DialogPrimitive.Close
            aria-label="Close"
            className="shadow-light text-grey-400 hover:text-grey-500 absolute top-4 right-4 flex size-11 items-center justify-center rounded-full bg-white transition-colors"
          >
            <XIcon className="size-5" />
          </DialogPrimitive.Close>
        )}
      </DialogPrimitive.Content>
    </ModalPortal>
  );
}

function ModalHeader({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn('flex w-full flex-col gap-2 pr-8', className)}
      {...props}
    />
  );
}

/**
 * The two modal shapes in the design system carry different titles: a form
 * modal ("Add Admin", "Announcements", 600x5xx) heads with the 32/44 h1, a
 * confirmation dialog ("Delete Route Group", "Log out", 600x180) with the
 * 20/28 h2. No default — picking one is a decision about which shape the
 * dialog is, and defaulting to the form size is how confirmations ended up
 * with a 32px title.
 */
const MODAL_TITLE_VARIANTS = {
  form: 'text-h1',
  confirmation: 'text-h2',
} as const;

type ModalTitleVariant = keyof typeof MODAL_TITLE_VARIANTS;

function ModalTitle({
  variant,
  className,
  ...props
}: React.ComponentProps<typeof DialogPrimitive.Title> & {
  variant: ModalTitleVariant;
}) {
  return (
    <DialogPrimitive.Title
      className={cn(
        MODAL_TITLE_VARIANTS[variant],
        'text-grey-500 font-bold',
        className
      )}
      {...props}
    />
  );
}

function ModalDescription({
  className,
  ...props
}: React.ComponentProps<typeof DialogPrimitive.Description>) {
  return (
    <DialogPrimitive.Description
      className={cn('text-p2 text-grey-400', className)}
      {...props}
    />
  );
}

function ModalFooter({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn('flex justify-between gap-3', className)} {...props} />
  );
}

export {
  Modal,
  ModalClose,
  ModalContent,
  ModalDescription,
  ModalFooter,
  ModalHeader,
  ModalTitle,
  ModalTrigger,
};
export type { ModalTitleVariant };
