import { type RefObject, useCallback, useEffect, useRef, useState } from 'react';

import { cn } from '@/lib/utils';

const DEFAULT_HIGHLIGHT_MS = 3000;

export interface UseRowHighlightReturn {
  /** Put on the element wrapping the table so rows can be scrolled into view. */
  containerRef: RefObject<HTMLDivElement | null>;
  /** Briefly highlight the row with this key and scroll it into view. */
  highlightRow: (key: string) => void;
  /** Pass to DataTable's getRowClassName to render the highlight. */
  getRowClassName: (key: string) => string;
}

/**
 * Briefly highlights a table row and scrolls it into view after it's added or
 * changed (e.g. create/duplicate/re-date). Pass the current `rows` so the
 * scroll retries once a refetch re-renders the table — the row often doesn't
 * exist in the DOM until the list data lands.
 *
 * Relies on DataTable tagging each row with `data-row-key` (its getRowKey).
 */
export function useRowHighlight(
  rows: unknown,
  durationMs = DEFAULT_HIGHLIGHT_MS
): UseRowHighlightReturn {
  const [highlightedKey, setHighlightedKey] = useState<string | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const containerRef = useRef<HTMLDivElement>(null);
  const scrolledRef = useRef<string | null>(null);

  const highlightRow = useCallback(
    (key: string) => {
      clearTimeout(timer.current);
      scrolledRef.current = null;
      setHighlightedKey(key);
      timer.current = setTimeout(() => setHighlightedKey(null), durationMs);
    },
    [durationMs]
  );

  // Runs again as `rows` updates because the row may not exist in the DOM (or
  // may re-sort) until the list refetch lands; scrolledRef keeps it to one
  // scroll per highlight.
  useEffect(() => {
    if (!highlightedKey || scrolledRef.current === highlightedKey) return;
    const row = containerRef.current?.querySelector(
      `[data-row-key="${highlightedKey}"]`
    );
    if (row) {
      scrolledRef.current = highlightedKey;
      row.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, [highlightedKey, rows]);

  const getRowClassName = useCallback(
    (key: string) =>
      cn(
        'transition-colors duration-500',
        key === highlightedKey && 'bg-blue-50'
      ),
    [highlightedKey]
  );

  return { containerRef, highlightRow, getRowClassName };
}
