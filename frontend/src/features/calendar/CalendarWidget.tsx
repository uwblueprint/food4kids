import {
  Button,
  Card,
  CardContent,
  CardHeader,
  Calendar,
} from '@/common/components';

export function CalendarWidget() {
  return (
    <Card className="shadow-admin-bento col-span-2 gap-4 rounded-4xl">
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
        <div></div>
        <div></div>
      </CardContent>
    </Card>
  );
}
