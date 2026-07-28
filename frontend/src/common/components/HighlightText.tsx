import { Fragment } from 'react';

interface HighlightTextProps {
  /** The full cell text. */
  text: string;
  /** The active search term; matches are highlighted case-insensitively. */
  query: string;
}

/** Escape a user-supplied string for safe literal use inside a RegExp. */
function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Renders `text` with every case-insensitive occurrence of `query` wrapped in a
 * light-blue highlight, like a browser's Ctrl+F. Falls back to plain text when
 * `query` is empty.
 */
export function HighlightText({ text, query }: HighlightTextProps) {
  const q = query.trim();
  if (!q) return <>{text}</>;

  const parts = text.split(new RegExp(`(${escapeRegExp(q)})`, 'gi'));
  return (
    <>
      {parts.map((part, i) =>
        part.toLowerCase() === q.toLowerCase() ? (
          <mark key={i} className="rounded bg-blue-100 text-inherit">
            {part}
          </mark>
        ) : (
          <Fragment key={i}>{part}</Fragment>
        )
      )}
    </>
  );
}
