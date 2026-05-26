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
