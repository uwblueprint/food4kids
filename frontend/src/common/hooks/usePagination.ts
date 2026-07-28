import { useState } from 'react';

/**
 * Rows per page for the admin tables. The Figma draws the table as a fixed box
 * of fourteen 54px cells — a header plus thirteen rows — with the page
 * switcher directly beneath it, so a full page fills the frame exactly.
 */
export const TABLE_PAGE_SIZE = 13;

export interface UsePaginationReturn {
  /** Current page, 1-indexed. Feed straight into the list query. */
  page: number;
  setPage: (page: number) => void;
}

/**
 * Pull `page` back inside range when the result set shrinks under it — delete
 * the only group on the last page, or assign the last unassigned route while
 * that filter is on, and the current page stops existing. Left alone the table
 * renders empty with no page marked current, and the reader has to work out
 * that they should click back.
 *
 * Call it after the list query, since only the response knows how many pages
 * there are now. Setting state during render is deliberate (the same pattern
 * usePagination uses for its reset): React re-renders with the corrected page
 * before committing, so the empty page is never painted.
 *
 * `totalPages` of 0 means "not loaded yet", not "no pages", so it never clamps.
 */
export function clampPage(
  page: number,
  totalPages: number,
  setPage: (page: number) => void
): number {
  if (totalPages >= 1 && page > totalPages) {
    setPage(totalPages);
    return totalPages;
  }
  return page;
}

/**
 * Page state for a server-paginated table.
 *
 * `resetKey` is whatever narrows the result set — the serialized search and
 * filter query. When it changes the page snaps back to 1: page 4 of an
 * unfiltered list is usually past the end of a filtered one, and a table that
 * renders empty the moment you type is worse than one that starts over.
 *
 * The reset is applied to the returned `page` immediately (not just to the
 * stored state) so the render that first sees the new key already asks for
 * page 1, rather than firing a throwaway request for the stale page.
 */
export function usePagination(resetKey: string): UsePaginationReturn {
  const [state, setState] = useState({ key: resetKey, page: 1 });

  const page = state.key === resetKey ? state.page : 1;
  if (state.key !== resetKey) setState({ key: resetKey, page: 1 });

  return { page, setPage: (next) => setState({ key: resetKey, page: next }) };
}
