import { isAxiosError } from 'axios';

import { describeApiFailure } from '@/api/errors';
import type { SystemSettingsUpdate } from '@/api/generated/types.gen';

/**
 * The settings keys whose value is a plain string.
 *
 * `keyof SystemSettingsUpdate` is too wide for a text input: it widens the
 * value type too, so writing a string to `boxes_per_car` would type-check.
 */
export type StringSettingKey = {
  [K in keyof SystemSettingsUpdate]-?: NonNullable<
    SystemSettingsUpdate[K]
  > extends string
    ? K
    : never;
}[keyof SystemSettingsUpdate];

/**
 * Settings that must hold a value before changes can be saved. One list drives
 * both the asterisk on the label and the save block; these columns are all
 * nullable server-side, so nothing else enforces it.
 */
export const REQUIRED_SETTING_KEYS = [
  'f4k_wr_email',
  'contact_phone',
  'f4k_wr_website',
  'f4k_wr_address',
] as const satisfies readonly StringSettingKey[];

/** Whitespace is not a value -- " " should not satisfy a required field. */
export function isBlank(value: string | null | undefined): boolean {
  return !value || !value.trim();
}

/**
 * Turn a failed settings PATCH into something worth showing an admin.
 *
 * `describeApiFailure` returns null for a 4xx, so surface the server's own
 * `detail` -- that is where the model validators put their reason.
 */
export function describeSaveFailure(error: unknown): string {
  const generic = describeApiFailure(error);
  if (generic) return generic;

  const detail = isAxiosError(error)
    ? (error.response?.data as { detail?: unknown } | undefined)?.detail
    : undefined;

  if (typeof detail === 'string') return detail;
  // FastAPI's 422 shape is a list of per-field objects, too raw to show as-is.
  return 'Some values were rejected. Check the highlighted fields and try again.';
}
