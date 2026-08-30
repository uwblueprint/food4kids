import type { SystemSettingsRead } from '@/api/generated/types.gen';

/**
 * What the import step should ask about delivery type. `pending` is its own
 * case on purpose: an unloaded settings query knows neither that there is one
 * type nor that there are several, and collapsing it into either would pick
 * for the admin or show a picker with nothing in it.
 */
export type DeliveryTypeSelection =
  | { kind: 'pending' }
  | { kind: 'unconfigured' }
  | { kind: 'only'; deliveryType: string }
  | { kind: 'choice'; deliveryTypes: string[] };

export function deliveryTypeSelection(
  settings: SystemSettingsRead | undefined
): DeliveryTypeSelection {
  if (!settings) return { kind: 'pending' };
  // The field is optional in the schema only because it has a server-side
  // default; an absent list is as unconfigured as an empty one.
  const deliveryTypes = settings.delivery_types ?? [];
  if (deliveryTypes.length === 0) return { kind: 'unconfigured' };
  if (deliveryTypes.length === 1)
    return { kind: 'only', deliveryType: deliveryTypes[0] };
  return { kind: 'choice', deliveryTypes };
}
