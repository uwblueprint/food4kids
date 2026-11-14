import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

import type { RouteWithDateRead } from '@/api/generated/types.gen';
import { useRoutes, useUpdateRoute } from '@/api/routes';
import {
  Button,
  Pagination,
  Popover,
  PopoverContent,
  PopoverTrigger,
  Spinner,
} from '@/common/components';
import { parseDateOnly, toNaiveDateString } from '@/common/utils';

import { ReassignDriverModal } from '../../routes/components/ReassignDriverModal';
import { AssignRouteModal } from './AssignRouteModal';

function currentWeek() {
  const monday = new Date();
  monday.setDate(monday.getDate() - (monday.getDay() || 7) + 1);
  const sunday = new Date(monday);
  sunday.setDate(monday.getDate() + 6);
  return { start: toNaiveDateString(monday), end: toNaiveDateString(sunday) };
}

function routeLabel(route: RouteWithDateRead) {
  return (
    <>
      <span>{route.name}</span>
      <span>
        {parseDateOnly(route.drive_date).toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
          year: 'numeric',
        })}
      </span>
      <span className="text-grey-400">{route.num_stops} stops</span>
    </>
  );
}

export function AssignedRoutesSection({
  driverId,
  driverName,
}: {
  driverId: string;
  driverName: string;
}) {
  const [editing, setEditing] = useState(false);
  const [assignOpen, setAssignOpen] = useState(false);
  const [actionRouteId, setActionRouteId] = useState<string | null>(null);
  const [reassignRoute, setReassignRoute] = useState<RouteWithDateRead | null>(
    null
  );
  const [message, setMessage] = useState('');
  const [page, setPage] = useState(1);
  const week = useMemo(() => currentWeek(), []);
  const { data, isPending, isError, isFetching, isPlaceholderData, refetch } =
    useRoutes({
      driver_id: driverId,
      start_date: week.start,
      end_date: week.end,
      order: 'asc',
      page,
      page_size: 20,
    });
  const unassignRoute = useUpdateRoute();
  const rowClass =
    'text-p3 grid w-full grid-cols-[1fr_auto_auto] items-start gap-3 py-2 text-left hover:text-blue-300';

  return (
    <section
      aria-labelledby="assigned-routes-heading"
      className="border-grey-200 rounded-xl border bg-white p-4"
    >
      <h3
        id="assigned-routes-heading"
        className="text-h3 text-grey-500 mb-1 font-bold"
      >
        Assigned Routes
      </h3>
      <p className="text-p3 text-grey-400 mb-3">This week</p>
      <p
        role="status"
        aria-atomic="true"
        className={`text-p3 text-grey-500 ${message || editing ? 'mb-2' : ''}`}
      >
        {message || (editing ? 'Select a route to edit' : '')}
      </p>
      {unassignRoute.isError && (
        <p role="alert" className="text-p3 text-red mb-2">
          Couldn&apos;t unassign this route. Please try again.
        </p>
      )}
      {isPending ? (
        <div className="flex justify-center py-4">
          <Spinner size="sm" />
        </div>
      ) : isError ? (
        <div role="alert">
          <p className="text-p3 text-grey-400">
            Couldn&apos;t load assigned routes.
          </p>
          <Button
            variant="textLink"
            disabled={isFetching}
            onClick={() => void refetch()}
          >
            Retry
          </Button>
        </div>
      ) : data?.items.length ? (
        <div
          className="divide-grey-200 flex flex-col divide-y"
          aria-busy={isFetching}
        >
          {data.items.map((route) =>
            editing ? (
              <Popover
                key={route.route_id}
                open={actionRouteId === route.route_id}
                onOpenChange={(open) =>
                  setActionRouteId(open ? route.route_id : null)
                }
              >
                <PopoverTrigger asChild>
                  <button
                    type="button"
                    disabled={unassignRoute.isPending || isPlaceholderData}
                    className={`${rowClass} cursor-pointer rounded-lg hover:bg-blue-50`}
                  >
                    {routeLabel(route)}
                  </button>
                </PopoverTrigger>
                <PopoverContent align="end" className="w-48 p-1">
                  <Button
                    variant="ghost"
                    className="h-auto w-full justify-start rounded-lg px-3 py-2"
                    disabled={unassignRoute.isPending}
                    onClick={() => {
                      unassignRoute.reset();
                      setMessage('');
                      unassignRoute.mutate(
                        {
                          path: { route_id: route.route_id },
                          body: { driver_id: null },
                        },
                        {
                          onSuccess: () => {
                            setActionRouteId(null);
                            setMessage(`${route.name} was unassigned.`);
                            setPage(1);
                          },
                        }
                      );
                    }}
                  >
                    {unassignRoute.isPending ? 'Unassigning…' : 'Unassign'}
                  </Button>
                  <Button
                    variant="ghost"
                    className="h-auto w-full justify-start rounded-lg px-3 py-2"
                    disabled={unassignRoute.isPending}
                    onClick={() => {
                      setActionRouteId(null);
                      setMessage('');
                      unassignRoute.reset();
                      setReassignRoute(route);
                    }}
                  >
                    Reassign
                  </Button>
                </PopoverContent>
              </Popover>
            ) : (
              <Link
                key={route.route_id}
                to={`/admin/routes/${route.route_id}`}
                className={rowClass}
              >
                {routeLabel(route)}
              </Link>
            )
          )}
        </div>
      ) : (
        <p className="text-p3 text-grey-400 py-3 text-center">
          No Assigned Routes
        </p>
      )}
      {!isError && data && (
        <fieldset
          disabled={isPlaceholderData || unassignRoute.isPending}
          className="min-w-0"
        >
          <Pagination
            page={page}
            totalPages={data.total_pages}
            onPageChange={(next) => {
              setPage(next);
              setActionRouteId(null);
            }}
            className="mt-3 gap-3"
          />
        </fieldset>
      )}
      <div className="mt-3 flex gap-3">
        {(editing || Boolean(data?.items.length)) && (
          <Button
            variant="tertiary"
            className="flex-1"
            aria-pressed={editing}
            disabled={unassignRoute.isPending}
            onClick={() => {
              setEditing(!editing);
              setActionRouteId(null);
              unassignRoute.reset();
              setMessage('');
            }}
          >
            {editing ? 'Done' : 'Edit'}
          </Button>
        )}
        <Button
          className="flex-1"
          disabled={unassignRoute.isPending}
          onClick={() => {
            setAssignOpen(true);
            setActionRouteId(null);
            setMessage('');
          }}
        >
          Assign
        </Button>
      </div>
      {assignOpen && (
        <AssignRouteModal
          driverId={driverId}
          driverName={driverName}
          onClose={() => setAssignOpen(false)}
          onAssigned={(name) => {
            setMessage(`${name} was assigned to ${driverName}.`);
            setPage(1);
          }}
        />
      )}
      {reassignRoute && (
        <ReassignDriverModal
          open
          onOpenChange={(open) => !open && setReassignRoute(null)}
          routeId={reassignRoute.route_id}
          routeGroupId={reassignRoute.route_group_id}
          currentDriverName={driverName}
          startTime={reassignRoute.start_time}
          contextLabel={`${reassignRoute.name} · ${reassignRoute.drive_date}`}
          showViewRoute={false}
          onUpdated={() => {
            setMessage(`${reassignRoute.name} was reassigned.`);
            setPage(1);
          }}
        />
      )}
    </section>
  );
}
