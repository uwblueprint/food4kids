import MegaphoneIcon from '@/assets/icons/megaphone.svg?react';
import SearchIcon from '@/assets/icons/search.svg?react';
import { Account, Button, Card, CardContent } from '@/common/components';
import { formatDisplayDate } from '@/common/utils';

const today = formatDisplayDate(new Date());

export const AdminHomePage = () => {
  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-start justify-between">
        <div className="flex flex-col items-start">
          <h1>Homepage</h1>
          <p className="text-p1 text-grey-400">{today}</p>
        </div>
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-4">
            <Button variant="tertiary" shape="circular">
              <MegaphoneIcon className="size-5 text-blue-300" />
            </Button>
            <Button variant="tertiary" shape="circular">
              <SearchIcon className="size-5 text-blue-300" />
            </Button>
          </div>
          <Account />
        </div>
      </div>
      <div className="grid grid-cols-3 gap-4">
        <Card className="col-span-2">
          <CardContent>TODO: Calendar</CardContent>
        </Card>
        <div className="flex flex-col gap-4">
          <Card>
            <CardContent>TODO: Route Generation Cost</CardContent>
          </Card>
          <Card>
            <CardContent>TODO: Statistics Toggles</CardContent>
          </Card>
        </div>
        <Card>
          <CardContent>TODO: Upcoming Routes</CardContent>
        </Card>
        <Card>
          <CardContent>TODO: Unassigned Routes</CardContent>
        </Card>
        <Card>
          <CardContent>TODO: Recent Notes</CardContent>
        </Card>
      </div>
    </div>
  );
};
