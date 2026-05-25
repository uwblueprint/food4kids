/**
 * PLANNED table contract for the admin routes "Groups" tab — NOT a live API shape.
 *
 * These fields describe what the designed table wants to show, but the backend
 * `GET /route-groups` does not yet return them. `RouteGroupRead` (generated)
 * currently only exposes name / notes / drive_date / num_routes; the aggregates
 * below (num_locations, num_boxes, num_drivers_assigned) and the derived
 * `status` / `delivery_type` need backend work before this can move onto the
 * generated client.
 *
 * Tracked in: F4KRP-196 (route-group aggregate endpoint). Until then this type
 * and `src/api/route-groups.ts` are an intentional WIP shell, not a converted
 * hook — do not treat this as mirroring a real endpoint.
 */
export type RouteStatus = 'Upcoming' | 'Completed' | 'Archived';
export type DeliveryType = 'School Year' | 'Summer';

export interface RouteGroupRow {
  id: string;
  name: string;
  date: string;
  delivery_type: string;
  num_routes: number;
  num_locations: number;
  num_boxes: number;
  num_drivers_assigned: number;
  status: RouteStatus;
}
