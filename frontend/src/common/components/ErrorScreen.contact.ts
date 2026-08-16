import { formatPhone } from '@/common/utils/phoneUtils';

/**
 * Build the "if this keeps happening, call someone" half of the catch-all
 * error message from whatever Settings has configured.
 *
 * All four combinations are reachable — `contact_name` and `contact_phone` are
 * independently nullable, and the page renders before the contact request
 * resolves — so the sentence has to stay grammatical in each. It is assembled
 * here rather than interpolated inline: with neither configured there is no one
 * to point at, so the sentence is dropped entirely instead of degrading into
 * "contact  at  for help."
 *
 * Lives beside `ErrorScreen.tsx` rather than in it (cf. `Button.variants.ts`)
 * because a module that exports both components and plain functions breaks Fast
 * Refresh.
 *
 * @returns the sentence, or `null` when there is no contact to name.
 */
export function contactSentence(
  name: string | null | undefined,
  phone: string | null | undefined
): string | null {
  const who = name?.trim() || null;
  // The stored value is RFC 3966; readers get the design's (519) 576-3443 form.
  const number = phone ? formatPhone(phone) : null;

  if (who && number)
    return `If the issue persists, contact ${who} at ${number} for help.`;
  if (who) return `If the issue persists, contact ${who} for help.`;
  if (number) return `If the issue persists, call ${number} for help.`;
  return null;
}
