import ChevronRightIcon from '@/assets/icons/chevron-right.svg?react';
import { cn } from '@/lib/utils';

/** Pages either side of the current one that always get their own button. */
const WINDOW = 1;

export interface PaginationProps {
  /** Current page, 1-indexed. */
  page: number;
  /** Total number of pages; the component renders nothing below 2. */
  totalPages: number;
  onPageChange: (page: number) => void;
  className?: string;
}

/**
 * Build the page list, using `null` for a gap.
 *
 * The first and last pages are always reachable, plus a window around the
 * current one — so page 1 of 10 reads "1 2 3 … 10" (what the Figma shows) and a
 * middle page reads "1 … 5 6 7 … 10". A gap of exactly one page renders as that
 * page rather than an ellipsis, since "…" standing in for a single number is
 * both wider and less useful than the number.
 */
function pageItems(page: number, totalPages: number): (number | null)[] {
  const shown = new Set([1, totalPages]);
  // Anchor the window at the start/end so the row keeps a stable width as you
  // page through: page 1 shows 1-3, the last page shows the final three.
  const start = Math.min(
    Math.max(page - WINDOW, 1),
    Math.max(totalPages - 2, 1)
  );
  for (let p = start; p < start + 1 + WINDOW * 2 && p <= totalPages; p += 1) {
    shown.add(p);
  }

  const sorted = [...shown].sort((a, b) => a - b);
  const items: (number | null)[] = [];
  for (const [i, p] of sorted.entries()) {
    const previous = sorted[i - 1];
    if (previous !== undefined) {
      if (p - previous === 2) items.push(previous + 1);
      else if (p - previous > 2) items.push(null);
    }
    items.push(p);
  }
  return items;
}

/**
 * Page switcher for the admin tables. Sits under the table, centred.
 *
 * Per the Figma the *current* page is the plain one (no fill, body text
 * colour) and every page you can navigate to carries a grey pill — the
 * highlight marks what is clickable, not where you are.
 */
export function Pagination({
  page,
  totalPages,
  onPageChange,
  className,
}: PaginationProps) {
  if (totalPages < 2) return null;

  const cell = 'flex size-7 items-center justify-center rounded-full text-p1';

  return (
    <nav
      aria-label="Pagination"
      className={cn('mt-7 flex items-center justify-center gap-6', className)}
    >
      {pageItems(page, totalPages).map((item, index) =>
        item === null ? (
          <span
            key={`gap-${index}`}
            aria-hidden
            className={cn(cell, 'bg-grey-200 font-medium text-blue-300')}
          >
            …
          </span>
        ) : (
          <button
            key={item}
            type="button"
            aria-label={`Page ${item}`}
            aria-current={item === page ? 'page' : undefined}
            onClick={() => onPageChange(item)}
            className={cn(
              cell,
              'font-medium transition-colors',
              item === page
                ? 'text-grey-500 cursor-default'
                : 'bg-grey-200 cursor-pointer text-blue-300 hover:bg-blue-50'
            )}
          >
            {item}
          </button>
        )
      )}

      {/* The Figma only draws this on page 1, where it is always available.
          Disabled rather than hidden on the last page so the row doesn't
          reflow under the pointer as you reach the end. */}
      <button
        type="button"
        disabled={page >= totalPages}
        onClick={() => onPageChange(page + 1)}
        className={cn(
          'text-p1 ml-3 flex items-center gap-2 font-medium transition-colors',
          page >= totalPages
            ? 'text-grey-400 cursor-not-allowed'
            : 'cursor-pointer text-blue-300 hover:underline'
        )}
      >
        Next
        <ChevronRightIcon className="size-5" />
      </button>
    </nav>
  );
}
