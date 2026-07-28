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
