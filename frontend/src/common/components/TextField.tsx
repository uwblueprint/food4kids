import {
  forwardRef,
  type InputHTMLAttributes,
  type ReactNode,
  useId,
} from 'react';

import { cn } from '@/lib/utils';

import { Field, FieldDescription, FieldLabel } from './Field';
import { Input } from './Input';

export interface TextFieldProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'id'> {
  label?: string;
  helperText?: string;
  error?: string;
  /** Non-editable info field: grey-150 bg, no border, read-only */
  info?: boolean;
  characterCount?: number;
  maxCharacters?: number;
  trailingIcon?: ReactNode;
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
      trailingIcon,
      className,
      disabled,
      required,
      id: idProp,
      ...props
    },
    ref,
  ) => {
    const autoId = useId();
    const id = idProp ?? autoId;
    const helperId = `${id}-helper`;
    const hasError = !!error;

    const isOverThreshold =
      characterCount !== undefined &&
      maxCharacters !== undefined &&
      characterCount >= maxCharacters * 0.8;

    return (
      <Field className={className}>
        {label && (
          <FieldLabel
            htmlFor={id}
            required={required}
            className={disabled ? 'opacity-50' : undefined}
          >
            {label}
          </FieldLabel>
        )}

        <div className="relative">
          <Input
            ref={ref}
            id={id}
            disabled={disabled}
            required={required}
            readOnly={info}
            maxLength={maxCharacters}
            aria-describedby={helperText || error ? helperId : undefined}
            aria-invalid={hasError || undefined}
            className={cn(
              hasError && 'outline-red focus:outline-red',
              info && 'bg-grey-150 cursor-default outline-none',
              trailingIcon && 'pr-9',
            )}
            {...props}
          />
          {trailingIcon && (
            <div className="text-grey-400 pointer-events-none absolute inset-y-0 right-3 flex items-center">
              {trailingIcon}
            </div>
          )}
        </div>

        <div className="flex items-start justify-between gap-2">
          {(helperText || error) && (
            <FieldDescription id={helperId} error={hasError}>
              {error ?? helperText}
            </FieldDescription>
          )}
          {maxCharacters !== undefined && (
            <p className={cn('text-p3 ml-auto shrink-0', isOverThreshold ? 'text-red' : 'text-grey-400')}>
              {characterCount ?? 0}/{maxCharacters}
            </p>
          )}
        </div>
      </Field>
    );
  },
);

TextField.displayName = 'TextField';

export { TextField };
