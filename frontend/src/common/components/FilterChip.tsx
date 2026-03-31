import type { ButtonHTMLAttributes, ReactNode } from 'react';

import { cn } from '@/lib/utils';

export interface FilterChipProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** Whether the chip is in its selected/active state */
  selected?: boolean;
}

function FilterChip({
  selected = false,
  className,
  children,
  ...props
}: FilterChipProps) {
  return (
    <button
      type="button"
      role="option"
      aria-selected={selected}
      className={cn(
        // Base
        'inline-flex items-center justify-center',
        'h-9 rounded-[40px] px-3',
        'text-p3 font-nunito font-bold',
        'cursor-pointer transition-colors',
        'outline-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-300',
        // Default state
        !selected && [
          'border-grey-300 bg-grey-200 text-grey-500 border',
          'hover:shadow-harsh',
        ],
        // Selected state
        selected && [
          'border border-blue-100 bg-blue-50 text-blue-300',
          'hover:shadow-harsh',
        ],
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}

export interface FilterChipGroupProps {
  /** Group heading displayed above the chips */
  label?: string;
  /** Chip elements */
  children: ReactNode;
  /** Additional className for the wrapper */
  className?: string;
  /** Show a top border delimiter (for stacking multiple groups) */
  showDelimiter?: boolean;
}

function FilterChipGroup({
  label,
  children,
  className,
  showDelimiter = false,
}: FilterChipGroupProps) {
  return (
    <div
      role="listbox"
      aria-label={label}
      className={cn(
        showDelimiter && 'border-grey-300 border-t pt-4',
        className
      )}
    >
      {label && (
        <p className="text-p3 text-grey-500 mb-2 font-semibold">{label}</p>
      )}
      <div className="flex flex-wrap gap-2">{children}</div>
    </div>
  );
}

export { FilterChip, FilterChipGroup };
