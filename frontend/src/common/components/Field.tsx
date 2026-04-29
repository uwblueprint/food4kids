import { type HTMLAttributes, type LabelHTMLAttributes } from 'react';

import AlertTriangle from '@/assets/icons/alert-triangle.svg?react';
import { cn } from '@/lib/utils';

function Field({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn('flex w-full flex-col gap-2', className)} {...props} />
  );
}

interface FieldLabelProps extends LabelHTMLAttributes<HTMLLabelElement> {
  required?: boolean;
}

function FieldLabel({
  className,
  required,
  children,
  ...props
}: FieldLabelProps) {
  return (
    <label
      className={cn('text-p1 text-grey-500 font-bold', className)}
      {...props}
    >
      {children}
      {required && <span className="text-red ml-0.5">*</span>}
    </label>
  );
}

interface FieldDescriptionProps extends HTMLAttributes<HTMLDivElement> {
  error?: boolean;
}

function FieldDescription({
  className,
  error,
  children,
  ...props
}: FieldDescriptionProps) {
  return (
    <div
      className={cn(
        'text-p2 flex items-center gap-1',
        error ? 'text-red' : 'text-grey-400',
        className
      )}
      {...props}
    >
      {error && (
        <AlertTriangle
          aria-hidden="true"
          className="text-red -mt-1 h-4 w-4 shrink-0"
        />
      )}
      <span>{children}</span>
    </div>
  );
}

export { Field, FieldLabel, FieldDescription };
