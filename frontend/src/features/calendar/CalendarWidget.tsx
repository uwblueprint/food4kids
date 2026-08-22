import { addDays, format, startOfWeek } from 'date-fns';
import { useMemo, useState } from 'react';

import ChevronLeftIcon from '@/assets/icons/chevron-left.svg?react';
import ChevronRightIcon from '@/assets/icons/chevron-right.svg?react';
import type { RouteWithDateRead } from '@/api/generated/types.gen';
import { useRoutes } from '@/api/routes';
import {
  Button,
  Card,
  CardContent,
  CardHeader,
  type Column,
  DataTable,
} from '@/common/components';
import { toNaiveDateString } from '@/common/utils';
import { cn } from '@/lib/utils';

function formatStartTime(value: string | null | undefined): string | null {
  if (!value) return null;
  const [h, m] = value.split(':');
  const hour = Number(h);
  const minute = Number(m);
  if (Number.isNaN(hour) || Number.isNaN(minute)) return null;
  const period = hour < 12 ? 'AM' : 'PM';
  const hour12 = hour % 12 === 0 ? 12 : hour % 12;
  return `${hour12}:${String(minute).padStart(2, '0')} ${period}`;
}

const COLUMNS: Column<RouteWithDateRead>[] = [
  { key: 'name', header: 'Name', render: (row) => row.name },
  { key: 'group_name', header: 'Route Group', render: (row) => row.group_name },
  {
    key: 'driver_name',
    header: 'Driver',
    render: (row) => row.driver_name ?? '—',
  },
  {
    key: 'start_time',
    header: 'Start Time',
    render: (row) => formatStartTime(row.start_time) ?? '—',
  },
  { key: 'num_stops', header: 'Stops', render: (row) => row.num_stops },
];

export function CalendarWidget() {
  const today = new Date();
  const [currentWeekStart, setCurrentWeekStart] = useState<Date>(() =>
    startOfWeek(today, { weekStartsOn: 1 })
  );

  const weekDays = Array.from({ length: 5 }, (_, index) => {
    const dayDate = addDays(currentWeekStart, index);
    return {
      dayName: format(dayDate, 'eee'),
      dayNumber: format(dayDate, 'd'),
      dateKey: toNaiveDateString(dayDate),
      dayDate,
    };
  });

  const initialSelectedKey =
    weekDays.find(
      (d) => format(d.dayDate, 'yyyy-MM-dd') === format(today, 'yyyy-MM-dd')
    )?.dateKey || weekDays[0].dateKey;

  const [selectedDateKey, setSelectedDateKey] =
    useState<string>(initialSelectedKey);

  const handlePrevWeek = () => {
    setCurrentWeekStart((prev) => {
      const newWeek = addDays(prev, -7);
      setSelectedDateKey(toNaiveDateString(newWeek));
      return newWeek;
    });
  };

  const handleNextWeek = () => {
    setCurrentWeekStart((prev) => {
      const newWeek = addDays(prev, 7);
      setSelectedDateKey(toNaiveDateString(newWeek));
      return newWeek;
    });
  };

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

  const selectedRoutes = routesByDay.get(selectedDateKey) ?? [];

  return (
    <Card className="shadow-admin-bento gap-4 rounded-4xl">
      <CardHeader className="flex-row items-center justify-between">
        <div>
          <h2 className="font-nunito text-h2 text-grey-500 font-bold">
            Calendar
          </h2>
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
      <CardContent className="flex flex-col gap-4">
        <div className="flex justify-between gap-3">
          {weekDays.map(({ dayName, dayNumber, dateKey }) => {
            const isSelected = selectedDateKey === dateKey;
            return (
              <Button
                key={dateKey}
                variant="secondary"
                onClick={() => setSelectedDateKey(dateKey)}
                className={cn(
                  `flex-1 ${
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
        <div>
          <DataTable
            columns={COLUMNS}
            rows={selectedRoutes}
            getRowKey={(row) => row.route_id}
            emptyState={
              <div className="text-grey-400 pt-8 pb-5 text-center">
                No routes scheduled for this day.
              </div>
            }
          />
        </div>
      </CardContent>
    </Card>
  );
}
