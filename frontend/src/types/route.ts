export type RouteDeliveryType = 'School Year' | 'Summer';

export type RouteStatus = 'Upcoming' | 'Completed' | 'Archived';

export interface Route {
  id: string;
  name: string;
  date: string;
  deliveryType: RouteDeliveryType;
  routeCount: number;
  locationCount: number;
  boxCount: number;
  driverCount: number;
  status: RouteStatus;
}
