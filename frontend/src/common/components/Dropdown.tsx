import { useId } from 'react';

import * as SelectPrimitive from '@radix-ui/react-select';
import AlertTriangle from '@/assets/icons/alert-triangle.svg?react';

import { cn } from '@/lib/utils';

export interface DropdownOption {
  label: string;
  value: string;
}

export interface DropdownProps {
  /** Field label displayed above the dropdown */
  label?: string;
  /** Placeholder text when no value is selected */
  placeholder?: string;
  /** List of selectable options */
  options: DropdownOption[];
  /** Currently selected value */
  value?: string;
  /** Callback when the selection changes */
  onValueChange?: (value: string) => void;
  /** Helper text below the dropdown */
  helperText?: string;
  /** Error message — replaces helperText and switches to error styling */
  error?: string;
  /** Disabled state */
  disabled?: boolean;
  /** Additional className for the outermost wrapper */
  className?: string;
  /** Override the auto-generated id */
  id?: string;
}

function Dropdown({
  label,
  placeholder = 'Select…',
  options,
  value,
  onValueChange,
  helperText,
  error,
  disabled = false,
  className,
  id: idProp,
}: DropdownProps) {
  const autoId = useId();
  const id = idProp ?? autoId;
  const helperId = `${id}-helper`;
  const hasError = !!error;

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

      {/* Select root */}
      <SelectPrimitive.Root
        value={value}
        onValueChange={onValueChange}
        disabled={disabled}
      >
        <SelectPrimitive.Trigger
          id={id}
          aria-describedby={helperText || error ? helperId : undefined}
          aria-invalid={hasError || undefined}
          className={cn(
            // Base
            'inline-flex h-[44px] w-full items-center justify-between rounded-lg px-3',
            'text-p2 text-grey-500 outline-none transition-colors',
            'cursor-pointer',
            // Default border & bg
            'border border-grey-300 bg-grey-100',
            // Focus / open
            'focus:border-blue-300 focus:ring-1 focus:ring-blue-300',
            'data-[state=open]:border-blue-300 data-[state=open]:ring-1 data-[state=open]:ring-blue-300',
            // Error
            hasError && 'border-red focus:border-red focus:ring-red',
            // Disabled
            disabled && 'bg-grey-150 text-grey-400 cursor-not-allowed opacity-60',
            // Placeholder color
            'data-[placeholder]:text-grey-400 data-[placeholder]:text-p3',
          )}
        >
          <SelectPrimitive.Value placeholder={placeholder} />
          <SelectPrimitive.Icon className="ml-2 shrink-0">
            <ChevronDownIcon />
          </SelectPrimitive.Icon>
        </SelectPrimitive.Trigger>

        {/* Dropdown content */}
        <SelectPrimitive.Portal>
          <SelectPrimitive.Content
            position="popper"
            sideOffset={4}
            className={cn(
              'z-50 w-[var(--radix-select-trigger-width)] overflow-hidden rounded-lg',
              'border border-grey-300 bg-grey-100 shadow-card',
              // Animation
              'data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:zoom-in-95',
              'data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95',
            )}
          >
            <SelectPrimitive.Viewport className="p-3">
              {options.map((opt) => (
                <SelectPrimitive.Item
                  key={opt.value}
                  value={opt.value}
                  className={cn(
                    'relative flex w-full cursor-pointer select-none items-center rounded-md px-3 py-2',
                    'text-p2 text-grey-500 outline-none',
                    'hover:bg-blue-50',
                    'focus:bg-blue-50',
                    // Selected item shows in blue
                    'data-[state=checked]:text-blue-300 data-[state=checked]:font-semibold',
                  )}
                >
                  <SelectPrimitive.ItemText>
                    {opt.label}
                  </SelectPrimitive.ItemText>
                </SelectPrimitive.Item>
              ))}
            </SelectPrimitive.Viewport>
          </SelectPrimitive.Content>
        </SelectPrimitive.Portal>
      </SelectPrimitive.Root>

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
    </div>
  );
}

/** Inline chevron-down SVG */
// TODO: This should be an icon component, not defined inline in this file (we also define this chevron in StyleGuidePage)
function ChevronDownIcon({ className = '' }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={cn('text-grey-400', className)}
      aria-hidden="true"
    >
      <polyline points="6 9 12 15 18 9" />
    </svg>
  );
}

export { Dropdown };