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
          /* Text Field spec (Figma): input text is 16px at every width —
           * Mobile/P2 (16/24 Regular) on mobile, Desktop/P1 (16/24 Medium)
           * from tablet up. Size is constant (text-m-p2); only the weight
           * steps up. Placeholder shares it (color only differs). */
          'text-m-p2 tablet:font-medium text-grey-500 placeholder:text-grey-400 font-normal',
          'w-full rounded-lg px-3 py-3',
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
