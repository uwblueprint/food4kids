import { isAxiosError } from 'axios';

import { describeApiFailure } from '@/api/errors';
import type { SystemSettingsUpdate } from '@/api/generated/types.gen';

/**
 * The settings keys whose value is a plain string.
 *
 * `keyof SystemSettingsUpdate` is too wide for a text input: it also covers
 * numbers (`boxes_per_car`), booleans (`announcement_emails_to_admins`), arrays
 * (`delivery_types`, `email_reminders`) and the import map. Because a key typed
 * as that whole union widens the value type to a union too, assigning a string
 * to a numeric column would type-check. Narrowing here makes a wrong key a
 * compile error instead, and removes the need to cast reads back to `string`.
 */
export type StringSettingKey = {
  [K in keyof SystemSettingsUpdate]-?: NonNullable<
    SystemSettingsUpdate[K]
  > extends string
    ? K
    : never;
}[keyof SystemSettingsUpdate];

/**
 * Settings that must hold a value before changes can be saved.
 *
 * The single source of truth for "required": it drives the red asterisk on the
 * label *and* the save block. Keeping one list is the point — an asterisk that
 * nothing enforces is worse than no asterisk, because it claims a guarantee the
 * column (all of these are nullable server-side) does not make.
 */
export const REQUIRED_SETTING_KEYS = [
  'f4k_wr_email',
  'contact_phone',
  'f4k_wr_website',
  'f4k_wr_address',
] as const satisfies readonly StringSettingKey[];

export type RequiredSettingKey = (typeof REQUIRED_SETTING_KEYS)[number];

/** Whitespace is not a value -- " " should not satisfy a required field. */
export function isBlank(value: string | null | undefined): boolean {
  return !value || !value.trim();
}

/**
 * Turn a failed settings PATCH into something worth showing an admin.
 *
 * `describeApiFailure` deliberately returns null for a 4xx, because only the
 * caller knows how to word "the server looked at your input and refused it".
 * For this form that means surfacing the server's own `detail`, which is where
 * the model validators (`EmailStr`, `validate_phone`, the delivery-type rules)
 * put their reason.
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
