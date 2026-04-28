import * as SelectPrimitive from '@radix-ui/react-select';
import { useId } from 'react';

import AlertTriangle from '@/assets/icons/alert-triangle.svg?react';
import ChevronDown from '@/assets/icons/chevron-down.svg?react';
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
    <div className={cn('flex w-full flex-col gap-2', className)}>
      {/* Label */}
      {label && (
        <label
          htmlFor={id}
          className={cn('text-p1 font-bold', disabled && 'opacity-50')}
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
            'inline-flex w-full items-center justify-between rounded-full px-5 py-2',
            'text-p2 text-grey-500 transition-colors outline-none',
            'cursor-pointer',
            // Default outline & bg
            'bg-grey-100 ring-grey-300 ring-1',
            // Focus / open
            'focus:ring-blue-300',
            'data-[state=open]:ring-blue-300',
            // Error
            hasError && 'ring-red focus:ring-red',
            // Disabled
            disabled &&
              'bg-grey-150 text-grey-400 cursor-not-allowed opacity-60',
            // Placeholder color
            'data-[placeholder]:text-grey-500'
          )}
        >
          <SelectPrimitive.Value placeholder={placeholder} />
          <SelectPrimitive.Icon className="ml-2 shrink-0">
            <ChevronDown className="text-grey-500 h-4 w-4" />
          </SelectPrimitive.Icon>
        </SelectPrimitive.Trigger>

        {/* Dropdown content */}
        <SelectPrimitive.Portal>
          <SelectPrimitive.Content
            position="popper"
            sideOffset={4}
            className={cn(
              'z-50 w-[var(--radix-select-trigger-width)] overflow-hidden rounded-lg',
              'border-grey-300 bg-grey-100 shadow-card border',
              // Animation
              'data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:zoom-in-95',
              'data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95'
            )}
          >
            <SelectPrimitive.Viewport className="p-3">
              {options.map((opt) => (
                <SelectPrimitive.Item
                  key={opt.value}
                  value={opt.value}
                  className={cn(
                    'relative flex w-full cursor-pointer items-center rounded-md px-3 py-2 select-none',
                    'text-p1 text-grey-500 outline-none',
                    'hover:bg-blue-50',
                    'focus:bg-blue-50',
                    // Selected item shows in blue
                    'data-[state=checked]:font-semibold data-[state=checked]:text-blue-300'
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
            'text-p2 flex w-full items-start gap-1',
            hasError ? 'text-red' : 'text-grey-400'
          )}
        >
          {hasError && (
            <AlertTriangle
              aria-hidden="true"
              className="text-red mt-0.5 h-4 w-4 shrink-0"
            />
          )}
          <span>{error ?? helperText}</span>
        </div>
      )}
    </div>
  );
}

export { Dropdown };
