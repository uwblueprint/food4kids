<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> 5e0c3ad (use get_current_database_user_id as announcement user_id)
import announcementsEmptyState from '@/assets/illustrations/announcements-empty-state.svg';
import { Button } from '@/common/components';
import { cn } from '@/lib/utils';

import {
  PANEL_PADDING_BOTTOM,
  PANEL_PADDING_X,
  PANEL_SECTION_GAP,
} from './utils';
=======
import boyAnnouncing from '@/assets/illustrations/boy-announcing.png';
import { Button } from '@/common/components';
<<<<<<< HEAD
>>>>>>> fa70cf5 (add board and crud functionality)
=======
import { cn } from '@/lib/utils';

import {
  PANEL_PADDING_BOTTOM,
  PANEL_PADDING_X,
  PANEL_SECTION_GAP,
} from './utils';
>>>>>>> b56351b (add bulk edit modal)

interface AnnouncementsEmptyStateProps {
  onCreateClick: () => void;
}

export function AnnouncementsEmptyState({
  onCreateClick,
}: AnnouncementsEmptyStateProps) {
  return (
<<<<<<< HEAD
<<<<<<< HEAD
    <div
      className={cn(
        'flex flex-1 flex-col items-center justify-center gap-8 text-center',
=======
    <div
      className={cn(
<<<<<<< HEAD
        'flex flex-1 flex-col items-center justify-center gap-6 text-center',
>>>>>>> b56351b (add bulk edit modal)
=======
        'flex flex-1 flex-col items-center justify-center gap-8 text-center',
>>>>>>> 5e0c3ad (use get_current_database_user_id as announcement user_id)
        PANEL_PADDING_X,
        PANEL_SECTION_GAP,
        PANEL_PADDING_BOTTOM
      )}
    >
<<<<<<< HEAD
      <img
        src={announcementsEmptyState}
        alt="No Announcements. The people wanna know what you have to say!"
        className="h-auto w-full max-w-[295px]"
        width={295}
        height={288}
      />
      <Button type="button" onClick={onCreateClick} className="w-full">
=======
    <div className="flex flex-1 flex-col items-center justify-center gap-6 px-6 py-12 text-center">
=======
>>>>>>> b56351b (add bulk edit modal)
      <img
        src={announcementsEmptyState}
        alt="No Announcements. The people wanna know what you have to say!"
        className="h-auto w-full max-w-[295px]"
        width={295}
        height={288}
      />
<<<<<<< HEAD
      <div className="flex flex-col gap-2">
        <p className="text-h2 text-grey-500 font-bold">No Announcements</p>
        <p className="text-p2 text-grey-400">
          The people wanna know what you have to say!
        </p>
      </div>
<<<<<<< HEAD
      <Button type="button" onClick={onCreateClick} className="w-full max-w-xs">
>>>>>>> fa70cf5 (add board and crud functionality)
=======
=======
>>>>>>> 5e0c3ad (use get_current_database_user_id as announcement user_id)
      <Button type="button" onClick={onCreateClick} className="w-full">
>>>>>>> b56351b (add bulk edit modal)
        Create Announcement
      </Button>
    </div>
  );
}
