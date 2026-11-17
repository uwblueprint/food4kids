import { useState } from 'react';

import type { RouteWithDateRead } from '@/api/generated/types.gen';
import { useRoutes, useUpdateRoute } from '@/api/routes';
import {
  Button,
  Field,
  FieldDescription,
  FieldLabel,
  Input,
  Modal,
  ModalContent,
  ModalDescription,
  ModalFooter,
  ModalHeader,
  ModalTitle,
  Pagination,
  Spinner,
  TimePicker,
} from '@/common/components';
import { fromApiTime, toApiTime } from '@/common/utils';
import { cn } from '@/lib/utils';

import { DEFAULT_START_TIME } from '../../routes/components/ReassignDriverModal';

interface AssignRouteModalProps {
  driverId: string;
  driverName: string;
  onClose: () => void;
  onAssigned: (routeName: string) => void;
}

/** Mounted for each opening so selection, search and errors start fresh. */
export function AssignRouteModal({
  driverId,
  driverName,
  onClose,
  onAssigned,
}: AssignRouteModalProps) {
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<RouteWithDateRead | null>(null);
  const [time, setTime] = useState(DEFAULT_START_TIME);
  const { data, isPending, isError, isPlaceholderData, isFetching, refetch } =
    useRoutes({
      unassigned_only: true,
      search: search.trim() || undefined,
      order: 'asc',
      page,
      page_size: 20,
    });
  const update = useUpdateRoute();
  const busy = update.isPending;
  const selectedRoute = data?.items.find(
    (route) => route.route_id === selected?.route_id
  );

  const selectRoute = (route: RouteWithDateRead) => {
    setSelected(route);
    setTime(fromApiTime(route.start_time) ?? DEFAULT_START_TIME);
    update.reset();
  };

  return (
    <Modal open onOpenChange={(open) => !open && !busy && onClose()}>
      <ModalContent className="max-h-[90dvh] w-[calc(100%-2rem)] overflow-y-auto">
        <ModalHeader>
          <ModalTitle variant="form">Assign Route</ModalTitle>
          <ModalDescription>
            Choose an unassigned route for {driverName}.
          </ModalDescription>
        </ModalHeader>
        <Field>
          <FieldLabel htmlFor="unassigned-route-search">
            Search routes
          </FieldLabel>
          <Input
            id="unassigned-route-search"
            placeholder="Search by route or group name"
            value={search}
            disabled={busy}
            onChange={(event) => {
              setSearch(event.target.value);
              setPage(1);
              setSelected(null);
              update.reset();
            }}
          />
        </Field>
        <fieldset disabled={busy || isPlaceholderData} className="min-w-0">
          <legend className="text-h3 text-grey-500 mb-2 font-bold">
            Unassigned routes
          </legend>
          <div
            className="border-grey-200 max-h-60 overflow-y-auto rounded-xl border"
            aria-busy={isFetching}
          >
            {isPending ? (
              <div className="flex justify-center p-6">
                <Spinner size="sm" />
              </div>
            ) : isError ? (
              <div role="alert" className="p-4">
                <p>Couldn&apos;t load unassigned routes.</p>
                <Button
                  variant="textLink"
                  disabled={isFetching}
                  onClick={() => void refetch()}
                >
                  Retry
                </Button>
              </div>
            ) : !data?.items.length ? (
              <p className="text-p2 text-grey-400 p-4">
                {search.trim()
                  ? 'No results. Try being less specific.'
                  : 'No unassigned routes available.'}
              </p>
            ) : (
              <ul
                className={cn(
                  'divide-grey-200 divide-y',
                  isPlaceholderData && 'opacity-50'
                )}
              >
                {data.items.map((route) => (
                  <li key={route.route_id}>
                    <label
                      htmlFor={`unassigned-route-${route.route_id}`}
                      className={cn(
                        'grid cursor-pointer grid-cols-[auto_1fr] items-start gap-x-3 p-3 hover:bg-blue-50',
                        selected?.route_id === route.route_id && 'bg-blue-50'
                      )}
                    >
                      <input
                        id={`unassigned-route-${route.route_id}`}
                        type="radio"
                        name="unassigned-route"
                        value={route.route_id}
                        checked={selected?.route_id === route.route_id}
                        onChange={() => selectRoute(route)}
                        className="row-span-2 mt-1 accent-blue-300"
                      />
                      <span className="text-p2 min-w-0 font-semibold break-words">
                        {route.name}
                      </span>
                      <span className="text-p3 text-grey-400 min-w-0 break-words">
                        {route.group_name} · {route.drive_date} ·{' '}
                        {route.num_stops} stops
                      </span>
                    </label>
                  </li>
                ))}
              </ul>
            )}
          </div>
          {!isError && data && (
            <Pagination
              page={page}
              totalPages={data.total_pages}
              onPageChange={(next) => {
                setPage(next);
                setSelected(null);
                update.reset();
              }}
              className="mt-3 gap-3"
            />
          )}
        </fieldset>
        <Field>
          <FieldLabel required>Start Time</FieldLabel>
          <TimePicker
            value={time}
            onChange={setTime}
            disabled={busy || !selectedRoute}
            className="w-full rounded-xl"
          />
        </Field>
        {update.isError && (
          <FieldDescription role="alert" error>
            Couldn&apos;t assign this route. Please try again.
          </FieldDescription>
        )}
        <ModalFooter>
          <Button variant="tertiary" disabled={busy} onClick={onClose}>
            Cancel
          </Button>
          <Button
            disabled={!selectedRoute || busy || isFetching || isError}
            onClick={() => {
              if (!selectedRoute || busy || isFetching || isError) return;
              update.mutate(
                {
                  path: { route_id: selectedRoute.route_id },
                  body: { driver_id: driverId, start_time: toApiTime(time) },
                },
                {
                  onSuccess: () => {
                    onAssigned(selectedRoute.name);
                    onClose();
                  },
                }
              );
            }}
          >
            {busy ? 'Assigning…' : 'Assign'}
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}
