import { addDays, format, startOfWeek } from 'date-fns';
import { useMemo, useState } from 'react';

import type { RouteWithDateRead } from '@/api/generated/types.gen';
import { useRoutes } from '@/api/routes';
import ChevronLeftIcon from '@/assets/icons/chevron-left.svg?react';
import ChevronRightIcon from '@/assets/icons/chevron-right.svg?react';
import {
  Button,
  Card,
  CardContent,
  CardHeader,
  type Column,
  DataTable,
} from '@/common/components';
import { AssignDriverCell } from '@/common/components';
import { formatStartTime, toNaiveDateString } from '@/common/utils';
import { cn } from '@/lib/utils';

function getRouteCellClassName(isFirst: boolean, isLast: boolean) {
  const isSingle = isFirst && isLast;

  if (isSingle) return 'text-p1 font-normal py-3';
  if (isFirst) return 'text-p1 font-normal pt-4.5 pb-4';
  if (isLast) return 'text-p1 font-normal pt-4 pb-3';
  return 'text-p1 font-normal py-4';
}

const HEADER_CLASS = 'font-medium h-auto pt-0 pb-2';

export function CalendarWidget() {
  const today = new Date();
  const [currentWeekStart, setCurrentWeekStart] = useState<Date>(() =>
    startOfWeek(today, { weekStartsOn: 1 })
  );

  // Weekends are explicitly not part of the design
  const weekDays = useMemo(() => {
    return Array.from({ length: 5 }, (_, index) => {
      const dayDate = addDays(currentWeekStart, index);
      return {
        dayName: format(dayDate, 'eee'),
        dayNumber: format(dayDate, 'd'),
        dateKey: toNaiveDateString(dayDate),
        dayDate,
      };
    });
  }, [currentWeekStart]);

  const initialSelectedKey =
    weekDays.find((d) => d.dateKey === toNaiveDateString(today))?.dateKey ||
    weekDays[0].dateKey;

  const [selectedDateKey, setSelectedDateKey] =
    useState<string>(initialSelectedKey);

  const goToWeek = (offset: number) => {
    const next = addDays(currentWeekStart, offset);
    setCurrentWeekStart(next);
    setSelectedDateKey(toNaiveDateString(next));
  };

  const handlePrevWeek = () => goToWeek(-7);
  const handleNextWeek = () => goToWeek(7);

  const { data } = useRoutes({
    start_date: toNaiveDateString(weekDays[0].dayDate),
    end_date: toNaiveDateString(weekDays[4].dayDate),
    page_size: 100,
  });

  const routesByDay = useMemo(() => {
    const items = data?.items ?? [];
    const map = new Map<string, RouteWithDateRead[]>();
    for (const day of weekDays) {
      map.set(day.dateKey, []);
    }
    for (const route of items) {
      const datePart = route.drive_date.split('T')[0];
      if (map.has(datePart)) {
        map.get(datePart)!.push(route);
      }
    }
    return map;
  }, [data?.items, weekDays]);

  const selectedRoutes = useMemo(() => {
    return routesByDay.get(selectedDateKey) ?? [];
  }, [routesByDay, selectedDateKey]);

  const columns: Column<RouteWithDateRead>[] = useMemo(() => {
    const getCellClassName = (row: RouteWithDateRead) => {
      const isFirst = selectedRoutes[0]?.route_id === row.route_id;
      const isLast =
        selectedRoutes[selectedRoutes.length - 1]?.route_id === row.route_id;
      return getRouteCellClassName(isFirst, isLast);
    };

    return [
      {
        key: 'name',
        header: 'Name',
        render: (row) => row.name,
        headerClassName: HEADER_CLASS,
        getCellClassName,
      },
      {
        key: 'group_name',
        header: 'Route Group',
        render: (row) => row.group_name,
        headerClassName: HEADER_CLASS,
        getCellClassName,
      },
      {
        key: 'driver_name',
        header: 'Driver',
        render: (row) => row.driver_name ?? <AssignDriverCell row={row} />,
        headerClassName: HEADER_CLASS,
        getCellClassName,
      },
      {
        key: 'start_time',
        header: 'Start Time',
        render: (row) => formatStartTime(row.start_time) ?? '—',
        headerClassName: HEADER_CLASS,
        getCellClassName,
      },
      {
        key: 'num_stops',
        header: 'Stops',
        render: (row) => row.num_stops,
        headerClassName: HEADER_CLASS,
        getCellClassName,
      },
    ];
  }, [selectedRoutes]);

  return (
    <Card className="shadow-admin-bento gap-4 rounded-4xl">
      <CardHeader className="flex-row items-start justify-between">
        <div>
          <h2 className="font-nunito text-h2 text-grey-500 font-bold">
            Calendar
          </h2>
          <p className="text-p1 text-grey-400">
            {format(weekDays[0].dayDate, 'MMM d, yyyy')} -{' '}
            {format(weekDays[4].dayDate, 'MMM d, yyyy')}
          </p>
        </div>
        <div className="flex items-center">
          <button
            type="button"
            aria-label="Previous week"
            onClick={handlePrevWeek}
            className="text-grey-400 hover:bg-grey-200 cursor-pointer rounded-full transition-colors focus-visible:outline-2 focus-visible:outline-blue-300"
          >
            <ChevronLeftIcon className="size-6" />
          </button>
          <button
            type="button"
            aria-label="Next week"
            onClick={handleNextWeek}
            className="text-grey-400 hover:bg-grey-200 cursor-pointer rounded-full transition-colors focus-visible:outline-2 focus-visible:outline-blue-300"
          >
            <ChevronRightIcon className="size-6" />
          </button>
        </div>
      </CardHeader>
      <CardContent className="flex min-h-0 flex-col gap-4">
        <div className="border-grey-200 flex justify-between gap-3 rounded-full border p-1">
          {weekDays.map(({ dayName, dayNumber, dateKey }) => {
            const isSelected = selectedDateKey === dateKey;
            return (
              <Button
                key={dateKey}
                variant="secondary"
                onClick={() => setSelectedDateKey(dateKey)}
                className={cn(
                  `flex-1 border-none bg-white ${
                    isSelected &&
                    'border-blue-200 bg-blue-50 text-blue-300 hover:bg-blue-100'
                  }`
                )}
              >
                {`${dayName} ${dayNumber}`}
              </Button>
            );
          })}
        </div>
        <div className="flex min-h-0">
          <DataTable
            columns={columns}
            rows={selectedRoutes}
            getRowKey={(row) => row.route_id}
            bodyClassName="divide-none"
            emptyState={
              <div className="text-grey-400 pt-8 pb-5 text-center">
                No routes scheduled for this day.
              </div>
            }
            className="flex-1 overflow-y-auto px-5 pt-4"
          />
        </div>
      </CardContent>
    </Card>
  );
}
