import { addDays, format, startOfWeek } from 'date-fns';
import { useState } from 'react';

import { Button, Card, CardContent, CardHeader } from '@/common/components';
import { cn } from '@/lib/utils';

export function CalendarWidget() {
  const today = new Date();
  const monday = startOfWeek(today, { weekStartsOn: 1 });
  const weekDays = Array.from({ length: 5 }, (_, index) => {
    const dayDate = addDays(monday, index);
    return {
      dayName: format(dayDate, 'eee'),
      dayNumber: format(dayDate, 'd'),
      dateKey: dayDate.toISOString(),
      dayDate,
    };
  });

  const initialSelectedKey =
    weekDays.find(
      (d) => format(d.dayDate, 'yyyy-MM-dd') === format(today, 'yyyy-MM-dd')
    )?.dateKey || weekDays[0].dateKey;

  const [selectedDateKey, setSelectedDateKey] =
    useState<string>(initialSelectedKey);

  return (
    <Card className="shadow-admin-bento gap-4 rounded-4xl">
      <CardHeader className="flex-row justify-between">
        <div>
          <h2 className="font-nunito text-h2 text-grey-500 font-bold">
            Calendar
          </h2>
          <h3>This week</h3>
        </div>
        <div className="flex gap-4">
          <Button variant="secondary">Print all routes</Button>
        </div>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div className="flex justify-between">
          {weekDays.map(({ dayName, dayNumber, dateKey }) => {
            const isSelected = selectedDateKey === dateKey;
            return (
              <Button
                key={dateKey}
                variant="secondary"
                onClick={() => setSelectedDateKey(dateKey)}
                className={cn(
                  isSelected &&
                    'border-blue-200 bg-blue-50 text-blue-300 hover:bg-blue-100'
                )}
              >
                {`${dayName} ${dayNumber}`}
              </Button>
            );
          })}
        </div>
        <div></div>
      </CardContent>
    </Card>
  );
}
