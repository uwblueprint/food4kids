import { Popover as PopoverPrimitive } from 'radix-ui';
import { useId } from 'react';

import CheckIcon from '@/assets/icons/check.svg?react';
import ChevronDownIcon from '@/assets/icons/chevron-down.svg?react';
import { cn } from '@/lib/utils';

interface MultiSelectProps {
  options: string[];
  value: string[];
  onChange: (next: string[]) => void;
  disabled?: boolean;
  /** Shown when nothing is selected. */
  placeholder?: string;
  className?: string;
  'aria-label'?: string;
}

/**
 * A checkbox list in a dropdown, for a field that takes several values.
 *
 * Distinct from {@link Dropdown}, which wraps Radix Select and can only hold
 * one value. The trigger summarises the selection the way the designs do:
 * the first choice, then "+N" for the rest.
 */
export function MultiSelect({
  options,
  value,
  onChange,
  disabled,
  placeholder = 'Select',
  className,
  'aria-label': ariaLabel,
}: MultiSelectProps) {
  const labelId = useId();
  const selected = options.filter((option) => value.includes(option));

  const toggle = (option: string) => {
    onChange(
      value.includes(option)
        ? value.filter((item) => item !== option)
        : [...options.filter((o) => value.includes(o) || o === option)]
    );
  };

  return (
    <PopoverPrimitive.Root>
      <PopoverPrimitive.Trigger
        disabled={disabled}
        aria-label={ariaLabel}
        className={cn(
          'border-grey-300 text-p2 text-grey-500 flex h-11 w-full items-center',
          'justify-between gap-2 rounded-[30px] border bg-white px-4',
          'disabled:bg-grey-150 disabled:text-grey-400 disabled:cursor-not-allowed',
          'focus-visible:outline-2 focus-visible:outline-blue-300',
          className
        )}
      >
        <span className="truncate">
          {selected.length === 0 ? (
            <span className="text-grey-400">{placeholder}</span>
          ) : (
            <>
              {selected[0]}
              {selected.length > 1 && (
                <span className="text-grey-400"> +{selected.length - 1}</span>
              )}
            </>
          )}
        </span>
        <ChevronDownIcon aria-hidden="true" className="size-4 shrink-0" />
      </PopoverPrimitive.Trigger>

      <PopoverPrimitive.Portal>
        <PopoverPrimitive.Content
          align="start"
          sideOffset={4}
          role="group"
          aria-labelledby={labelId}
          className={cn(
            'border-grey-300 z-50 max-h-64 overflow-y-auto rounded-xl border',
            'bg-white p-1 shadow-md',
            'w-[var(--radix-popover-trigger-width)]'
          )}
        >
          <span id={labelId} className="sr-only">
            {ariaLabel ?? placeholder}
          </span>
          {options.map((option) => {
            const checked = value.includes(option);
            return (
              <label
                key={option}
                className="text-p2 text-grey-500 flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2 hover:bg-blue-50"
              >
                <span
                  className={cn(
                    'flex size-4 shrink-0 items-center justify-center rounded border',
                    checked
                      ? 'text-grey-100 border-blue-300 bg-blue-300'
                      : 'border-grey-300'
                  )}
                >
                  {checked && (
                    <CheckIcon aria-hidden="true" className="size-3" />
                  )}
                </span>
                <input
                  type="checkbox"
                  className="sr-only"
                  checked={checked}
                  onChange={() => toggle(option)}
                />
                {option}
              </label>
            );
          })}
        </PopoverPrimitive.Content>
      </PopoverPrimitive.Portal>
    </PopoverPrimitive.Root>
  );
}
