import SearchIcon from '@/assets/icons/search.svg?react';
import { Account, Button, Card, CardContent } from '@/common/components';
import { formatDisplayDate } from '@/common/utils';
import { AnnouncementsBoard } from '@/features/announcements';
import { StatisticsWidget } from '@/features/statistics';

const today = formatDisplayDate(new Date());

/** Every bento tile: 28px corners and the soft admin-page shadow. */
const TILE = 'shadow-admin-bento rounded-4xl';

export const AdminHomePage = () => {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-start justify-between">
        <div className="flex flex-col items-start">
          <h1>Homepage</h1>
          <p className="text-p1 text-grey-400">{today}</p>
        </div>
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-4">
            <AnnouncementsBoard />
            <Button variant="tertiary" shape="circularLarge">
              <SearchIcon className="size-[22px] text-blue-300" />
            </Button>
          </div>
          <Account />
        </div>
      </div>
      {/* The bento: a 331px right rail with the calendar and unassigned-routes
          tiles taking the rest, on 468px and 376px rows. Only the right rail is
          fixed — the left tiles grow with the viewport. */}
      <div className="grid grid-cols-[1fr_331px] grid-rows-[468px_376px] gap-5">
        <Card className={TILE}>
          <CardContent>TODO: Calendar</CardContent>
        </Card>
        <div className="grid grid-rows-[121px_1fr] gap-5">
          <Card className={TILE}>
            <CardContent>TODO: Route Generation Cost</CardContent>
          </Card>
          <StatisticsWidget />
        </div>
        <Card className={TILE}>
          <CardContent>TODO: Unassigned Routes</CardContent>
        </Card>
        <Card className={TILE}>
          <CardContent>TODO: Recent Notes</CardContent>
        </Card>
      </div>
    </div>
  );
};
