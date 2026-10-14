/**
 * Convert between the API's `"HH:MM:SS"` times and the `"HH:MM"` that
 * {@link TimePicker} speaks, so neither side has to know the other's format.
 */

export const toApiTime = (value: string): string => `${value}:00`;

/** `undefined` when there is nothing stored, so callers pick their own default. */
export const fromApiTime = (
  value: string | null | undefined
): string | undefined => (value ? value.slice(0, 5) : undefined);
