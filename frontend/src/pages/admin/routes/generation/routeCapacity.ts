import type { SystemSettingsRead } from '@/api/generated/types.gen';

/**
 * The three configured numbers `/jobs/generate` requires, read off the settings
 * row. They have no server-side defaults — omitting one is a 422 — so this
 * returns `null` rather than a partial object whenever they can't be supplied:
 * settings still loading, or a capacity too small to size a route. Callers gate
 * the request on a non-null result, which is what stops a body going out with a
 * key missing.
 */
export interface RouteCapacity {
  max_boxes_per_driver: number;
  children_per_box: number;
  service_time_minutes: number;
}

export function routeCapacity(
  settings: SystemSettingsRead | undefined
): RouteCapacity | null {
  const maxBoxesPerDriver = settings?.boxes_per_car;
  const childrenPerBox = settings?.children_per_box;
  const serviceTimeMinutes = settings?.dropoff_minutes;
  if (
    maxBoxesPerDriver === undefined ||
    childrenPerBox === undefined ||
    serviceTimeMinutes === undefined ||
    maxBoxesPerDriver < 1 ||
    childrenPerBox < 1 ||
    serviceTimeMinutes < 0
  ) {
    return null;
  }
  return {
    max_boxes_per_driver: maxBoxesPerDriver,
    children_per_box: childrenPerBox,
    service_time_minutes: serviceTimeMinutes,
  };
}
