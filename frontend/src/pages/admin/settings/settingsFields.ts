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

/** The server's reason for rejecting a value, keyed by the column it names. */
export type SettingFieldErrors = Partial<
  Record<keyof SystemSettingsUpdate, string>
>;

function responseDetail(error: unknown): unknown {
  return isAxiosError(error)
    ? (error.response?.data as { detail?: unknown } | undefined)?.detail
    : undefined;
}

/** Pydantic prefixes a custom validator's message; the admin doesn't need it. */
function readableMessage(message: string): string {
  const text = message.replace(/^Value error,\s*/, '').trim();
  if (!text) return 'This value was rejected.';
  const sentence = text[0].toUpperCase() + text.slice(1);
  return /[.!?]$/.test(sentence) ? sentence : `${sentence}.`;
}

/**
 * The per-field reasons inside FastAPI's 422 body.
 *
 * `detail` is a list of `{ loc: ["body", "<column>"], msg }`. Only an entry
 * naming exactly one column is kept: a nested path (`email_reminders.0.
 * days_before`) has no single input to sit on, and guessing one would put the
 * message against the wrong control.
 */
export function fieldErrorsFrom(error: unknown): SettingFieldErrors {
  const detail = responseDetail(error);
  if (!Array.isArray(detail)) return {};

  const errors: SettingFieldErrors = {};
  for (const entry of detail) {
    const { loc, msg } = (entry ?? {}) as { loc?: unknown; msg?: unknown };
    if (!Array.isArray(loc) || loc.length !== 2 || loc[0] !== 'body') continue;
    if (typeof loc[1] !== 'string' || typeof msg !== 'string') continue;

    const key = loc[1] as keyof SystemSettingsUpdate;
    // First one wins: a field with two complaints only has room for one.
    errors[key] ??= readableMessage(msg);
  }
  return errors;
}

/**
 * Turn a failed settings PATCH into something worth showing an admin.
 *
 * `describeApiFailure` returns null for a 4xx, so surface the server's own
 * `detail` -- that is where the model validators put their reason.
 */
export function describeSaveFailure(
  error: unknown,
  fieldErrors: SettingFieldErrors
): string {
  const generic = describeApiFailure(error);
  if (generic) return generic;

  const detail = responseDetail(error);
  if (typeof detail === 'string') return detail;

  // Only promise highlighting when a field actually carries the message --
  // otherwise this sends the admin looking for an outline that isn't there.
  return Object.keys(fieldErrors).length > 0
    ? 'Some values were rejected. Check the highlighted fields and try again.'
    : 'Some values were rejected. Check your changes and try again.';
}
