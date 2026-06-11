import boyAnnouncing from '@/assets/illustrations/boy-announcing.png';
import { Button } from '@/common/components';
import { cn } from '@/lib/utils';

import {
  PANEL_PADDING_BOTTOM,
  PANEL_PADDING_X,
  PANEL_SECTION_GAP,
} from './utils';

interface AnnouncementsEmptyStateProps {
  onCreateClick: () => void;
}

export function AnnouncementsEmptyState({
  onCreateClick,
}: AnnouncementsEmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-1 flex-col items-center justify-center gap-6 text-center',
        PANEL_PADDING_X,
        PANEL_SECTION_GAP,
        PANEL_PADDING_BOTTOM
      )}
    >
      <img
        src={boyAnnouncing}
        alt=""
        className="h-40 w-auto md:h-48"
      />
      <div className="flex flex-col gap-2">
        <p className="text-h2 text-grey-500 font-bold">No Announcements</p>
        <p className="text-p2 text-grey-400">
          The people wanna know what you have to say!
        </p>
      </div>
      <Button type="button" onClick={onCreateClick} className="w-full">
        Create Announcement
      </Button>
    </div>
  );
}
