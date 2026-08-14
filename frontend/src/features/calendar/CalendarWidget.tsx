import { Card, CardContent, Calendar } from '@/common/components';

export function CalendarWidget() {
  return (
    <Card className="shadow-admin-bento col-span-2 rounded-4xl">
      <CardContent className="flex flex-col gap-4">
        <h2 className="font-nunito text-h2 text-grey-500 font-bold">
          Calendar
        </h2>
        <Calendar mode="single" />
      </CardContent>
    </Card>
  );
}
