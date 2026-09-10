import { describe, expect, it } from 'vitest';

import type { SystemSettingsRead } from '@/api/generated/types.gen';

import { routeCapacity } from './routeCapacity';

function settings(
  overrides: Partial<SystemSettingsRead> = {}
): SystemSettingsRead {
  return {
    system_settings_id: 'settings-id',
    boxes_per_car: 10,
    children_per_box: 2,
    dropoff_minutes: 3,
    ...overrides,
  } as SystemSettingsRead;
}

describe('routeCapacity', () => {
  it('carries the configured numbers through unchanged', () => {
    expect(
      routeCapacity(
        settings({ boxes_per_car: 7, children_per_box: 3, dropoff_minutes: 4 })
      )
    ).toEqual({
      max_boxes_per_driver: 7,
      children_per_box: 3,
      service_time_minutes: 4,
    });
  });

  it('substitutes nothing of its own', () => {
    // The bug this guards: a default here would outrank the configured value.
    const capacity = routeCapacity(settings({ boxes_per_car: 14 }));
    expect(capacity?.max_boxes_per_driver).toBe(14);
    expect(
      routeCapacity(settings({ boxes_per_car: 10 }))?.max_boxes_per_driver
    ).toBe(10);
  });

  it('is null while settings are still loading', () => {
    // The original failure: posting before the query resolved dropped the key
    // from the body entirely, and the server filled in its own number.
    expect(routeCapacity(undefined)).toBeNull();
  });

  it.each([
    ['boxes_per_car', { boxes_per_car: undefined }],
    ['children_per_box', { children_per_box: undefined }],
    ['dropoff_minutes', { dropoff_minutes: undefined }],
  ])('is null when %s is absent', (_name, overrides) => {
    expect(routeCapacity(settings(overrides))).toBeNull();
  });

  it.each([
    ['a car that holds no boxes', { boxes_per_car: 0 }],
    ['a negative capacity', { boxes_per_car: -1 }],
    ['a zero box divisor', { children_per_box: 0 }],
    ['a negative dropoff time', { dropoff_minutes: -1 }],
  ])('is null for %s', (_name, overrides) => {
    expect(routeCapacity(settings(overrides))).toBeNull();
  });

  it('accepts a zero dropoff time, which settings allow', () => {
    expect(routeCapacity(settings({ dropoff_minutes: 0 }))).toEqual({
      max_boxes_per_driver: 10,
      children_per_box: 2,
      service_time_minutes: 0,
    });
  });

  it('never returns a partial object', () => {
    // Whatever comes back is complete, so spreading it can't leave a key out.
    const capacity = routeCapacity(settings());
    expect(capacity).not.toBeNull();
    expect(Object.keys(capacity!).sort()).toEqual([
      'children_per_box',
      'max_boxes_per_driver',
      'service_time_minutes',
    ]);
  });
});
