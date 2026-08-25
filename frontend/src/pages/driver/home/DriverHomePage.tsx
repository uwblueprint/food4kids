import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { useAuthStore } from '@/api/authStore';
import { useDriverHistorySummary } from '@/api/drivers';
import { useDriverRoutes, useRoute } from '@/api/routes';
import noUpcoming from '@/assets/illustrations/boy-edge-case-with-questions.png';
import noPast from '@/assets/illustrations/girl-confused.png';
import logo from '@/assets/logos/logo_mobile_one_line.svg';
import { StatisticsCard } from '@/common/components/StatisticsCard';
import { AnnouncementsBoard } from '@/features/announcements';

import { RouteCard } from './components';

// Wrapper component to fetch route details and render RouteCard
function RouteCardWithDetails({
  routeId,
  title,
  date,
  isPast,
}: {
  routeId: string;
  title: string;
  isPast?: boolean;
  date: string;
}) {
  const { data: routeDetails } = useRoute(routeId);

  // Debug logging removed: avoid console calls in production UI

  return (
    <RouteCard
      title={title}
      routeId={routeId}
      date={date}
      encodedPolyline={routeDetails?.encoded_polyline || ''}
      stops={routeDetails?.stops}
      isPast={isPast}
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
  const [tab, setTab] = useState<'upcoming' | 'past'>('upcoming');

  return (
    <main className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <img src={logo} alt="food4kids WATERLOO REGION" className="h-10" />
        <div className="flex items-center gap-4">
          <AnnouncementsBoard />
          <button
            onClick={() => navigate('/driver/profile')}
            className="flex size-11 cursor-pointer items-center justify-center rounded-full bg-blue-300 font-bold text-white transition-opacity hover:opacity-90"
          >
            {user?.firstName?.[0]}
            {user?.lastName?.[0]}
          </button>
        </div>
      </div>

      <h1 className="text-h1 text-grey-500 font-bold">
        Hello, {user?.firstName || 'Driver'}!
      </h1>

      <div className="grid grid-cols-2 gap-4">
        <StatisticsCard
          label="This Year"
          value={`${(driverStats?.current_year_km || 0).toFixed(1)} km`}
          character="granny"
          color="green"
        />
        <StatisticsCard
          label="Lifetime"
          value={`${(driverStats?.lifetime_km || 0).toFixed(1)} km`}
          character="boy"
          color="blue"
        />
      </div>
      {/* Segmented control (pill) - visible on all sizes */}
      <div className="mb-2 w-full">
        <div className="bg-grey-150 w-full rounded-full p-1">
          <div className="flex w-full rounded-full">
            <button
              onClick={() => setTab('upcoming')}
              className={
                (tab === 'upcoming'
                  ? 'bg-blue-50 text-blue-300'
                  : 'text-grey-500') +
                ' text-p2 flex-1 rounded-full px-4 py-3 text-center font-semibold'
              }
            >
              Upcoming
            </button>
            <button
              onClick={() => setTab('past')}
              className={
                (tab === 'past'
                  ? 'bg-blue-50 text-blue-300'
                  : 'text-grey-500') +
                ' text-p2 flex-1 rounded-full px-4 py-3 text-center font-semibold'
              }
            >
              Past
            </button>
          </div>
        </div>
      </div>

      {/* Content: render selected tab's routes using a responsive grid */}
      <div>
        {tab === 'upcoming' ? (
          upcomingRoutes.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16">
              <img
                src={noUpcoming}
                alt="No upcoming routes"
                className="mx-auto h-40 w-auto"
              />
              <h3 className="text-h3 text-grey-500 mt-6 font-bold">
                Routes not found
              </h3>
              <p className="text-p2 text-grey-500 mt-2">
                You have no upcoming routes.
              </p>
            </div>
          ) : (
            <div className="tablet:grid-cols-2 grid grid-cols-1 gap-4">
              {upcomingRoutes.map((route) => (
                <RouteCardWithDetails
                  key={route.route_id}
                  routeId={route.route_id}
                  title={route.name}
                  date={`${formatDate(route.drive_date)} · ${formatTime(route.start_time)} · ${route.num_stops} stops`}
                  isPast={false}
                />
              ))}
            </div>
          )
        ) : tab === 'past' ? (
          pastRoutes.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16">
              <img
                src={noPast}
                alt="No past routes"
                className="mx-auto h-40 w-auto"
              />
              <h3 className="text-h3 text-grey-500 mt-6 font-bold">
                Routes not found
              </h3>
              <p className="text-p2 text-grey-500 mt-2">
                You have no past routes.
              </p>
            </div>
          ) : (
            <div className="tablet:grid-cols-2 grid grid-cols-1 gap-4">
              {pastRoutes.map((route) => (
                <RouteCardWithDetails
                  key={route.route_id}
                  routeId={route.route_id}
                  title={route.name}
                  date={`${formatDate(route.drive_date)} · ${formatTime(route.start_time)} · ${route.num_stops} stops`}
                  isPast={true}
                />
              ))}
            </div>
          )
        ) : null}
      </div>
    </main>
  );
};
