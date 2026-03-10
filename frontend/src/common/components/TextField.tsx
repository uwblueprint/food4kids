import { type InputHTMLAttributes, forwardRef, useId } from 'react';

import AlertTriangle from '@/assets/icons/alert-triangle.svg?react';

import { cn } from '@/lib/utils';

export interface TextFieldProps
  extends Omit<InputHTMLAttributes<HTMLInputElement>, 'id'> {
  /** Field label displayed above the input */
  label?: string;
  /** Helper or info text below the input */
  helperText?: string;
  /** Error message — replaces helperText and switches to error styling */
  error?: string;
  /** Non-editable info field: grey-150 bg, no border, read-only */
  info?: boolean;
  /** Current character count (displayed as "count/max") */
  characterCount?: number;
  /** Max characters allowed (used for display and threshold warning) */
  maxCharacters?: number;
  /** Override the auto-generated id */
  id?: string;
}

const TextField = forwardRef<HTMLInputElement, TextFieldProps>(
  (
    {
      label,
      helperText,
      error,
      info = false,
      characterCount,
      maxCharacters,
      className,
      disabled,
      id: idProp,
      ...props
    },
    ref,
  ) => {
    const autoId = useId();
    const id = idProp ?? autoId;
    const helperId = `${id}-helper`;
    const hasError = !!error;

    // Character count threshold: red when ≥80% of max
    const isOverThreshold =
      characterCount !== undefined &&
      maxCharacters !== undefined &&
      characterCount >= maxCharacters * 0.8;

    return (
      <div className={cn('flex w-full flex-col gap-1', className)}>
        {/* Label */}
        {label && (
          <label
            htmlFor={id}
            className={cn(
              'text-p3 text-grey-400',
              disabled && 'opacity-50',
            )}
          >
            {label}
          </label>
        )}

        {/* Input */}
        <input
          ref={ref}
          id={id}
          disabled={disabled}
          readOnly={info}
          aria-describedby={helperText || error ? helperId : undefined}
          aria-invalid={hasError || undefined}
          className={cn(
            // Base
            'text-p2 text-grey-500 placeholder:text-p3 placeholder:text-grey-400',
            'h-[44px] w-full rounded-lg px-3',
            'outline-none transition-colors',
            // Default state
            'border border-grey-300 bg-grey-100',
            // Focus / active
            'focus:border-blue-300 focus:ring-1 focus:ring-blue-300',
            // Error
            hasError && 'border-red focus:border-red focus:ring-red',
            // Info (non-editable)
            info && 'border-none bg-grey-150 cursor-default',
            // Disabled
            disabled && 'bg-grey-150 text-grey-400 cursor-not-allowed opacity-60',
            // Mobile height
            'md:h-[44px]',
          )}
          {...props}
        />

        {/* Bottom row: helper/error text + character count */}
        <div className="flex items-start justify-between gap-2">
          {/* Helper or error text */}
          {(helperText || error) && (
            <div
              id={helperId}
              className={cn(
                'text-p2 flex w-full items-center gap-1',
                hasError ? 'text-red' : 'text-grey-400',
              )}
            >
              {hasError && (
                <AlertTriangle
                  aria-hidden="true"
                  className="h-4 w-4 shrink-0 -mt-1 text-red"
                />
              )}
              <span>{error ?? helperText}</span>
            </div>
          )}

          {/* Character count */}
          {maxCharacters !== undefined && (
            <p
              className={cn(
                'text-p3 ml-auto shrink-0',
                isOverThreshold ? 'text-red' : 'text-grey-400',
              )}
            >
              {characterCount ?? 0}/{maxCharacters}
            </p>
          )}
        </div>
      </div>
    );
  },
);

TextField.displayName = 'TextField';

export { TextField };