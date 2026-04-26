import { cva, type VariantProps } from 'class-variance-authority';
import { forwardRef, type InputHTMLAttributes } from 'react';

import searchIcon from '@/assets/icons/search.svg';
import { cn } from '@/lib/utils';

const searchBarVariants = cva(
  /* Base styles shared by all variants */
  [
    'flex h-[44px] w-full items-center gap-2 rounded-full px-4',
    'transition-colors',
    'focus-within:ring-1 focus-within:ring-blue-300',
  ],
  {
    variants: {
      variant: {
        default: 'bg-white shadow-sm',
        filled: 'border border-grey-300 bg-grey-150',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
);

export interface SearchBarProps
  extends
    Omit<InputHTMLAttributes<HTMLInputElement>, 'type'>,
    VariantProps<typeof searchBarVariants> {
  /** Additional className for the outermost wrapper */
  wrapperClassName?: string;
}

const SearchBar = forwardRef<HTMLInputElement, SearchBarProps>(
  ({ variant, className, wrapperClassName, ...props }, ref) => {
    return (
      <div className={cn(searchBarVariants({ variant }), wrapperClassName)}>
        {/* Search icon */}
        <img
          src={searchIcon}
          alt=""
          aria-hidden="true"
          className="h-[18px] w-[18px] shrink-0 opacity-80"
        />

        {/* Input */}
        <input
          ref={ref}
          type="search"
          className={cn(
            'h-full w-full bg-transparent outline-none',
            'text-p2 text-grey-500 placeholder:text-p2 placeholder:text-grey-400',
            // Remove default search input styling (x button, etc.)
            '[&::-webkit-search-cancel-button]:hidden',
            '[&::-webkit-search-decoration]:hidden',
            className
          )}
          {...props}
        />
      </div>
    );
  }
);

SearchBar.displayName = 'SearchBar';

export { SearchBar };
