export type RouteDeliveryType = 'School' | 'Family';

export type RouteStatus = 'Upcoming' | 'Completed' | 'Archived';

/** Matches backend app.models.route.Route serialization. */
export interface Route {
  route_id: string;
  name: string;
  notes: string;
  length: number;
  encoded_polyline: string | null;
  polyline_updated_at: string | null;
  expires_at: string | null;
  ends_at_warehouse: boolean;
  note_chain_id: string | null;
}