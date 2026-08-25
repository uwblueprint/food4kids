import { Link, useParams } from 'react-router-dom';

import ChevronRightIcon from '@/assets/icons/chevron-right.svg?react';
import { Account, Spinner } from '@/common/components';
import { RouteMap } from '@/common/components/RouteMap';
import { useRoute } from '@/common/hooks/useRoute';
import { AnnouncementsBoard } from '@/features/announcements';

import { RouteOverviewCard } from './components/RouteOverviewCard';
import { StopsTable } from './components/StopsTable';

const statusWrapper =
  'flex w-full items-center justify-center rounded-2xl border border-grey-300 bg-grey-150 p-8';

/**
 * Admin view of a single route — overview, editable stops, and map — reached
 * by clicking a row on the Routes tab (/admin/routes/:routeId).
 */
export function AdminIndividualRoutePage() {
  const { routeId } = useParams<{ routeId: string }>();
  const { data: route, isLoading, isError, error } = useRoute(routeId);

  return (
    <div className="flex flex-col gap-8">
      {/* Header: breadcrumb + account */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-1">
          <Link
            to="/admin/routes?tab=routes"
            className="text-h1 text-grey-400 cursor-pointer font-bold"
          >
            Routes
          </Link>
          <ChevronRightIcon className="text-grey-400 size-8 shrink-0" />
          <span className="text-h1 text-grey-500 font-bold">
            {route?.name || 'Route'}
          </span>
        </div>
        <div className="flex items-center gap-6">
          <AnnouncementsBoard />
          <Account />
        </div>
      </div>

      {isLoading ? (
        <div className={statusWrapper}>
          <Spinner />
        </div>
      ) : isError || !route ? (
        <div className={`${statusWrapper} text-p2 text-grey-500`}>
          {isError
            ? `Failed to load route: ${error.message}`
            : 'Route not found.'}
        </div>
      ) : (
        <>
          <RouteOverviewCard route={route} />
          <StopsTable route={route} />

          {/* Map View */}
          <section className="flex flex-col gap-4">
            <h2 className="text-h2 font-nunito-sans text-grey-500 font-bold">
              Map View
            </h2>
            <RouteMap
              encodedPolyline={route.encoded_polyline}
              className="desktop:h-[408px] tablet:h-[320px] h-[240px]"
            />
          </section>
        </>
      )}
    </div>
  );
}
