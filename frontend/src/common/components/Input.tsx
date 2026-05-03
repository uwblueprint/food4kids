import { forwardRef, type InputHTMLAttributes } from 'react';

import { cn } from '@/lib/utils';

import { FieldDescription } from './Field';

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  description?: string;
  error?: string;
  characterCount?: number;
  maxCharacters?: number;
  wrapperClassName?: string;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      className,
      type,
      description,
      error,
      characterCount,
      maxCharacters,
      wrapperClassName,
      ...props
    },
    ref
  ) => {
    const hasError = !!error;
    const isExpanded = description || error || maxCharacters !== undefined;
    const isOverThreshold =
      characterCount !== undefined &&
      maxCharacters !== undefined &&
      characterCount >= maxCharacters * 0.8;

    const input = (
      <input
        ref={ref}
        type={type}
        maxLength={maxCharacters}
        className={cn(
          'text-p2 text-grey-500 placeholder:text-p1 placeholder:text-grey-400',
          'w-full rounded-lg px-6 py-3',
          'transition-colors',
          'bg-grey-100 outline-grey-300 outline outline-1 outline-offset-[-1px]',
          'focus:outline-2 focus:outline-blue-300',
          'disabled:bg-grey-150 disabled:text-grey-400 disabled:cursor-not-allowed disabled:opacity-60',
          hasError && 'outline-red focus:outline-red',
          className
        )}
        {...props}
      />
    );

    if (!isExpanded) return input;

    return (
      <div className={cn('flex flex-col gap-2', wrapperClassName)}>
        {input}
        <div className="flex items-start justify-between gap-2">
          {(description || error) && (
            <FieldDescription error={hasError}>
              {error ?? description}
            </FieldDescription>
          )}
          {maxCharacters !== undefined && (
            <p
              className={cn(
                'text-p3 ml-auto shrink-0',
                isOverThreshold ? 'text-red' : 'text-grey-400'
              )}
            >
              {characterCount ?? 0}/{maxCharacters}
            </p>
          )}
        </div>
      </div>
    );
  }
);

Input.displayName = 'Input';

export { Input };
