import type { ReactNode } from 'react';

/**
 * Wraps an interactive cell (the assign pill, the kebab, the date picker) so
 * its clicks and keyboard activation (Enter/Space) don't bubble to a clickable
 * row — the row is a keyboard-operable button, so a nested control's keydown
 * would otherwise fire the row's action instead.
 */
export function RowActionCell({ children }: { children: ReactNode }) {
  return (
    <span
      className="inline-block"
      role="presentation"
      onClick={(e) => e.stopPropagation()}
      onKeyDown={(e) => e.stopPropagation()}
    >
      {children}
    </span>
  );
}
