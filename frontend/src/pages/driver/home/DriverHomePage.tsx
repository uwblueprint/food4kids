import { useNavigate } from 'react-router-dom';
import logo from '@/assets/logos/logo_mobile_one_line.svg';
import { StatisticsCard } from '@/common/components/StatisticsCard';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/common/components/Tabs';
import { AnnouncementsBoard } from '@/features/announcements';
import { RouteCard } from './components';
import { useAuthStore } from '@/api/authStore';
import { useDriverHistorySummary } from '@/api/drivers';
import { useDriverRoutes, useRoute } from '@/api/routes';

// Wrapper component to fetch route details and render RouteCard
function RouteCardWithDetails({
  routeId,
  title,
  date,
}: {
  routeId: string;
  title: string;
  date: string;
}) {
  const { data: routeDetails } = useRoute(routeId);

  // Log for debugging - expand the object to see all fields
  console.log(
    'RouteCardWithDetails - routeId:',
    routeId,
    'routeDetails:',
    JSON.stringify(routeDetails, null, 2)
  );

  return (
    <RouteCard
      title={title}
      date={date}
      encodedPolyline={routeDetails?.encoded_polyline || ''}
      stops={routeDetails?.stops}
    />
  );
}

export const DriverHomePage = () => {
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);
  const driverId = user?.driverId;

  // Only fetch driver stats if we have a driverId
  const { data: driverStats } = useDriverHistorySummary(
    driverId || '',
    !!driverId // Only enable query when driverId exists
  );
  const { data: routesData } = useDriverRoutes();

  // Filter routes into upcoming vs past based on drive_date
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const routes = routesData?.items || [];
  const upcomingRoutes = routes.filter((route) => {
    const driveDate = new Date(route.drive_date);
    return driveDate >= today;
  });
  const pastRoutes = routes.filter((route) => {
    const driveDate = new Date(route.drive_date);
    return driveDate < today;
  });

  // Format date for display
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    });
  };

  // Format time for display
  const formatTime = (timeString: string | null) => {
    if (!timeString) return '';
    const [hours, minutes] = timeString.split(':');
    const hour = parseInt(hours, 10);
    const ampm = hour >= 12 ? 'PM' : 'AM';
    const hour12 = hour % 12 || 12;
    return `${hour12}:${minutes} ${ampm}`;
  };
  return (
    <main className="flex flex-col gap-8">
      <div className="flex items-center justify-between">
        <img src={logo} alt="food4kids WATERLOO REGION" className="h-10" />
        <div className="flex items-center gap-4">
          <AnnouncementsBoard />
          <div
            onClick={() => navigate('/driver/profile')}
            className="flex size-10 cursor-pointer items-center justify-center rounded-full bg-blue-300 font-bold text-white transition-opacity hover:opacity-90"
          >
            {user?.firstName?.[0]}
            {user?.lastName?.[0]}
          </div>
        </div>
      </div>

      <h1 className="text-h1 text-grey-500 font-bold">
        Hello, {user?.firstName || 'Driver'}!
      </h1>

      <div className="tablet:grid-cols-2 grid grid-cols-1 gap-4">
        <StatisticsCard
          label="This Year"
          value={`${(driverStats?.current_year_km || 0).toFixed(1)} km`}
          character="boyPointing"
          color="blue"
        />
        <StatisticsCard
          label="Lifetime"
          value={`${(driverStats?.lifetime_km || 0).toFixed(1)} km`}
          character="granny"
          color="green"
        />
      </div>

      <Tabs defaultValue="upcoming">
        <TabsList>
          <TabsTrigger value="upcoming">Upcoming</TabsTrigger>
          <TabsTrigger value="past">Past</TabsTrigger>
        </TabsList>

        <TabsContent value="upcoming">
          <div className="tablet:grid-cols-2 grid grid-cols-1 gap-4">
            {upcomingRoutes.length === 0 ? (
              <p className="text-p2 text-grey-500">No upcoming routes</p>
            ) : (
              upcomingRoutes.map((route) => (
                <RouteCardWithDetails
                  key={route.route_id}
                  routeId={route.route_id}
                  title={route.name}
                  date={`${formatDate(route.drive_date)} · ${formatTime(route.start_time)} · ${route.num_stops} stops`}
                />
              ))
            )}
          </div>
        </TabsContent>

        <TabsContent value="past">
          <div className="tablet:grid-cols-2 grid grid-cols-1 gap-4">
            {pastRoutes.length === 0 ? (
              <p className="text-p2 text-grey-500">No past routes</p>
            ) : (
              pastRoutes.map((route) => (
                <RouteCardWithDetails
                  key={route.route_id}
                  routeId={route.route_id}
                  title={route.name}
                  date={`${formatDate(route.drive_date)} · ${formatTime(route.start_time)} · ${route.num_stops} stops`}
                />
              ))
            )}
          </div>
        </TabsContent>
      </Tabs>
    </main>
  );
};
