import { addDays, format, startOfWeek } from 'date-fns';
import { useMemo, useState } from 'react';

import type { RouteWithDateRead } from '@/api/generated/types.gen';
import { useRoutes } from '@/api/routes';
import CalendarIcon from '@/assets/icons/calendar.svg?react';
import ChevronLeftIcon from '@/assets/icons/chevron-left.svg?react';
import ChevronRightIcon from '@/assets/icons/chevron-right.svg?react';
import {
  AssignDriverCell,
  Button,
  Calendar,
  Card,
  CardContent,
  CardHeader,
  type Column,
  DataTable,
  Modal,
  ModalContent,
  ModalHeader,
  ModalTitle,
} from '@/common/components';
import {
  formatStartTime,
  parseDateOnly,
  toNaiveDateString,
} from '@/common/utils';
import { cn } from '@/lib/utils';

function getRouteCellClassName(isFirst: boolean, isLast: boolean) {
  const isSingle = isFirst && isLast;

  if (isSingle) return 'text-p1 font-normal py-2';
  if (isFirst) return 'text-p1 font-normal pt-3.5 pb-3';
  if (isLast) return 'text-p1 font-normal pt-3 pb-2';
  return 'text-p1 font-normal py-3';
}

const HEADER_CLASS = 'font-medium h-auto pt-0 pb-2';

const ICON_BUTTON_CLASS =
  'text-grey-400 hover:bg-grey-200 cursor-pointer rounded-full p-1 transition-colors focus-visible:outline-2 focus-visible:outline-blue-300';

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

  const [isDatePickerOpen, setIsDatePickerOpen] = useState(false);

  const handleGoToDate = (date: Date) => {
    setCurrentWeekStart(startOfWeek(date, { weekStartsOn: 1 }));
    setSelectedDateKey(toNaiveDateString(date));
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
        render: (row) => row.driver_name ?? (
          <div className="flex h-[.9lh] items-center">
            <AssignDriverCell row={row} />
          </div>
        ),
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
    <Card className="shadow-admin-bento gap-6 rounded-4xl">
      <CardHeader className="flex-row items-center justify-between -mt-1">
        <h2 className="font-nunito text-h2 text-grey-500 font-bold">
          Calendar
        </h2>
        <div className="flex items-center gap-2">
          <p className="text-p1 text-grey-400">
            {format(weekDays[0].dayDate, 'MMM d, yyyy')} -{' '}
            {format(weekDays[4].dayDate, 'MMM d, yyyy')}
          </p>
          <button
            type="button"
            aria-label="Open calendar"
            onClick={() => setIsDatePickerOpen(true)}
            className={cn(ICON_BUTTON_CLASS, '-mt-1')}
          >
            <CalendarIcon className="size-5" />
          </button>
        </div>
      </CardHeader>
      <CardContent className="flex min-h-0 flex-col gap-4">
        <div className="flex items-center gap-2">
          <button
            type="button"
            aria-label="Previous week"
            onClick={handlePrevWeek}
            className={ICON_BUTTON_CLASS}
          >
            <ChevronLeftIcon className="size-6 -mt-3" />
          </button>
          <div className="border-grey-200 flex flex-1 justify-between gap-3 rounded-full border p-.5 -mt-4">
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
                      'border-blue-200 bg-blue-50 font-bold text-blue-300 hover:bg-blue-100'
                    }`
                  )}
                >
                  {`${dayName} ${dayNumber}`}
                </Button>
              );
            })}
          </div>
          <button
            type="button"
            aria-label="Next week"
            onClick={handleNextWeek}
            className={ICON_BUTTON_CLASS}
          >
            <ChevronRightIcon className="size-6 -mt-3" />
          </button>
        </div>
        <div className="flex min-h-0 -mt-2">
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
            className="flex-1 overflow-y-auto px-5 pt-3"
          />
        </div>
      </CardContent>
      <Modal open={isDatePickerOpen} onOpenChange={setIsDatePickerOpen}>
        <ModalContent className="h-[450px] max-w-[600px]">
          <ModalHeader>
            <ModalTitle variant="confirmation">Go to date</ModalTitle>
          </ModalHeader>
          <Calendar
            mode="single"
            selected={parseDateOnly(selectedDateKey)}
            defaultMonth={parseDateOnly(selectedDateKey)}
            disabled={{ dayOfWeek: [0, 6] }}
            onSelect={(date) => {
              if (!date) return;
              handleGoToDate(date);
              setIsDatePickerOpen(false);
            }}
            weekStartsOn={0}
            // Fill the modal: each level stretches into the space left over,
            // the week rows split it evenly, and each day is a circle as tall
            // as its row. Resizing the modal resizes the whole grid.
            classNames={{
              root: 'flex min-h-0 w-full flex-1 flex-col',
              months: 'relative flex min-h-0 flex-1 flex-col',
              month: 'flex min-h-0 w-full flex-1 flex-col gap-4',
              month_grid: 'flex min-h-0 w-full flex-1 flex-col',
              weeks: 'flex min-h-0 flex-1 flex-col',
              week: 'mt-1 flex min-h-0 w-full flex-1',
              day: 'relative flex min-h-0 flex-1 items-center justify-center p-0 select-none',
              day_button: 'h-full! w-auto! aspect-square max-w-full min-w-0',
            }}
            className="p-0"
          />
        </ModalContent>
      </Modal>
    </Card>
  );
}
