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
  ...props
}: React.ComponentProps<typeof DialogPrimitive.Content>) {
  return (
    <ModalPortal>
      <ModalOverlay />
      <DialogPrimitive.Content
        className={cn(
          'fixed top-1/2 left-1/2 z-50 w-full max-w-[600px] -translate-x-1/2 -translate-y-1/2',
          'bg-grey-100 shadow-harsh rounded-2xl p-6',
          'flex flex-col items-stretch gap-4',
          'data-[state=open]:animate-in data-[state=closed]:animate-out',
          'data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0',
          'data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95',
          className
        )}
        {...props}
      >
        {children}
        <DialogPrimitive.Close
          aria-label="Close"
          className="text-grey-400 hover:text-grey-500 absolute top-6 right-6 transition-colors"
        >
          <XIcon className="size-5" />
        </DialogPrimitive.Close>
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

function ModalTitle({
  className,
  ...props
}: React.ComponentProps<typeof DialogPrimitive.Title>) {
  return (
    <DialogPrimitive.Title
      className={cn('text-h2 text-grey-500 font-bold', className)}
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
      className={cn('text-p2 text-grey-400 font-normal', className)}
      {...props}
    />
  );
}

function ModalFooter({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('flex justify-end gap-3', className)} {...props} />;
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
