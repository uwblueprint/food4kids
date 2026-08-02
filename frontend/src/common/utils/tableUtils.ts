/**
 * Render an empty table cell as the design's hyphen.
 *
 * Empty means null/undefined, the empty string, or a zero count — a group with
 * no routes yet reads "-", not "0", because the routes haven't been generated
 * rather than counted to nothing. Shared so every admin table uses one
 * character; the tables previously mixed "-" and "—".
 */
export const orDash = (value: string | number | null | undefined): string =>
  value === null || value === undefined || value === '' || value === 0
    ? '-'
    : String(value);
