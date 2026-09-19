import { formatPhone } from '@/common/utils/phoneUtils';

/**
 * The "if it keeps happening, call someone" line, or `null` if there's no one
 * to name. Both fields are independently nullable, so all four combinations
 * have to stay grammatical.
 *
 * Its own file because mixing component and non-component exports breaks Fast
 * Refresh (cf. `Button.variants.ts`).
 */
export function contactSentence(
  name: string | null | undefined,
  phone: string | null | undefined
): string | null {
  const who = name?.trim() || null;
  const number = phone ? formatPhone(phone) : null;

  if (who && number)
    return `If the issue persists, contact ${who} at ${number} for help.`;
  if (who) return `If the issue persists, contact ${who} for help.`;
  if (number) return `If the issue persists, call ${number} for help.`;
  return null;
}
