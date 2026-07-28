import type { ReactNode } from 'react';

import FilterLinesIcon from '@/assets/icons/filter-lines.svg?react';
import type { UseSearchReturn } from '@/common/hooks';

import { Button } from './Button';
import { SearchBar } from './SearchBar';

interface TableToolbarProps {
  /** Search input state from useSearch. */
  search: UseSearchReturn;
  searchPlaceholder?: string;
  /** Render the filter button (left of nothing, right of search). */
  showFilter?: boolean;
  /** Filter button click handler; omit for an inert placeholder button. */
  onFilterClick?: () => void;
  /** Tints the filter button when a filter is applied. */
  hasActiveFilters?: boolean;
  /** Right-aligned action buttons (e.g. "Generate Routes", add, share). */
  actions?: ReactNode;
}

/**
 * Standard toolbar above the admin data tables: a search box, an optional
 * filter button, and a slot for right-aligned actions. Shared so every table
 * page (Groups, Routes, Addresses, …) gets the same layout.
 */
export function TableToolbar({
  search,
  searchPlaceholder = 'Search anything',
  showFilter = false,
  onFilterClick,
  hasActiveFilters = false,
  actions,
}: TableToolbarProps) {
  return (
    <div className="mb-7 flex items-center justify-between">
      <div className="flex items-center gap-5">
        <SearchBar placeholder={searchPlaceholder} {...search} />
        {showFilter && (
          <Button
            variant="tertiary"
            shape="circular"
            aria-label="Filters"
            className={hasActiveFilters ? 'bg-blue-50' : 'bg-white'}
            onClick={onFilterClick}
          >
            <FilterLinesIcon className="size-5" />
          </Button>
        )}
      </div>
      {actions && <div className="flex items-center gap-4">{actions}</div>}
    </div>
  );
}
