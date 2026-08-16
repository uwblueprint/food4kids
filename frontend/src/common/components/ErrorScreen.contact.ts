import { formatPhone } from '@/common/utils/phoneUtils';

/**
 * Build the "if this keeps happening, call someone" half of the catch-all
 * error message.
 *
 * Both fields are independently nullable and the page renders before the query
 * resolves, so all four combinations are reachable and each needs to stay
 * grammatical — hence a function rather than an inline template that would
 * produce "contact  at  for help."
 *
 * Split out of `ErrorScreen.tsx` (cf. `Button.variants.ts`) because mixing
 * component and non-component exports breaks Fast Refresh.
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
