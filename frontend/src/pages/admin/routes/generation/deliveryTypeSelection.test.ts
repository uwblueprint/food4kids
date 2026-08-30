import { describe, expect, it } from 'vitest';

import type { SystemSettingsRead } from '@/api/generated/types.gen';

import { deliveryTypeSelection } from './deliveryTypeSelection';

const settings = (delivery_types: string[] | undefined): SystemSettingsRead =>
  ({ delivery_types }) as unknown as SystemSettingsRead;

describe('deliveryTypeSelection', () => {
  it('reports pending while the settings query has no data', () => {
    // Not "none" and not "many": the count is unknown until settings arrive.
    expect(deliveryTypeSelection(undefined)).toEqual({ kind: 'pending' });
  });

  it('reports unconfigured for an empty list', () => {
    expect(deliveryTypeSelection(settings([]))).toEqual({
      kind: 'unconfigured',
    });
  });

  it('reports unconfigured when the field is absent', () => {
    expect(deliveryTypeSelection(settings(undefined))).toEqual({
      kind: 'unconfigured',
    });
  });

  it('applies the only type when exactly one is configured', () => {
    expect(deliveryTypeSelection(settings(['Family']))).toEqual({
      kind: 'only',
      deliveryType: 'Family',
    });
  });

  it('offers a choice for two or more types, in configured order', () => {
    expect(deliveryTypeSelection(settings(['Family', 'School']))).toEqual({
      kind: 'choice',
      deliveryTypes: ['Family', 'School'],
    });
    expect(
      deliveryTypeSelection(settings(['School', 'Family', 'Pantry']))
    ).toEqual({
      kind: 'choice',
      deliveryTypes: ['School', 'Family', 'Pantry'],
    });
  });

  it('never treats a single type as a choice, whatever its name', () => {
    for (const name of ['Family', 'x', 'A very long delivery type name']) {
      expect(deliveryTypeSelection(settings([name]))).toEqual({
        kind: 'only',
        deliveryType: name,
      });
    }
  });
});
