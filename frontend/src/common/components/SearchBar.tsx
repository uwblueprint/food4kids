import { type InputHTMLAttributes, forwardRef } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';

import { cn } from '@/lib/utils';

const searchBarVariants = cva(
  /* Base styles shared by all variants */
  [
    'flex h-[44px] w-full items-center gap-2 rounded-lg px-3',
    'transition-colors',
    'focus-within:border-blue-300 focus-within:ring-1 focus-within:ring-blue-300',
  ],
  {
    variants: {
      variant: {
        default: 'border border-grey-300 bg-grey-100',
        filled: 'border border-grey-300 bg-grey-150',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  },
);

export interface SearchBarProps
  extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type'>,
    VariantProps<typeof searchBarVariants> {
  /** Additional className for the outermost wrapper */
  wrapperClassName?: string;
}

const SearchBar = forwardRef<HTMLInputElement, SearchBarProps>(
  ({ variant, className, wrapperClassName, ...props }, ref) => {
    return (
      <div
        className={cn(searchBarVariants({ variant }), wrapperClassName)}
      >
        {/* Search icon */}
        <SearchIcon />

        {/* Input */}
        <input
          ref={ref}
          type="search"
          className={cn(
            'h-full w-full bg-transparent outline-none',
            'text-p2 text-grey-500 placeholder:text-p3 placeholder:text-grey-400',
            // Remove default search input styling (x button, etc.)
            '[&::-webkit-search-cancel-button]:hidden',
            '[&::-webkit-search-decoration]:hidden',
            className,
          )}
          {...props}
        />
      </div>
    );
  },
);

SearchBar.displayName = 'SearchBar';

/** Inline search (magnifying glass) SVG */
// TODO: See if we can have a search icon that we can use instead
function SearchIcon({ className = '' }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={cn('shrink-0 text-grey-400', className)}
      aria-hidden="true"
    >
      <circle cx="11" cy="11" r="8" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" />
    </svg>
  );
}

export { SearchBar };