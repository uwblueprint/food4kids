import { forwardRef, type TextareaHTMLAttributes } from 'react';

import { cn } from '@/lib/utils';

import { FieldDescription } from './Field';

export interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  description?: string;
  error?: string;
  characterCount?: number;
  maxCharacters?: number;
  wrapperClassName?: string;
}

const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  (
    {
      className,
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

    const textarea = (
      <textarea
        ref={ref}
        maxLength={maxCharacters}
        className={cn(
          'text-p2 text-grey-500 placeholder:text-p1 placeholder:text-grey-400',
          'min-h-[120px] w-full resize-y rounded-lg px-3 py-3',
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

    if (!isExpanded) return textarea;

    return (
      <div className={cn('flex flex-col gap-2', wrapperClassName)}>
        {textarea}
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

Textarea.displayName = 'Textarea';

export { Textarea };
