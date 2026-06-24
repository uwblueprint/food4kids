import announcementsEmptyState from '@/assets/illustrations/announcements-empty-state.svg';
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
        'flex flex-1 flex-col items-center justify-center gap-8 text-center',
        PANEL_PADDING_X,
        PANEL_SECTION_GAP,
        PANEL_PADDING_BOTTOM
      )}
    >
      <img
        src={announcementsEmptyState}
        alt=""
        aria-hidden
        className="h-auto w-full max-w-[295px]"
        width={295}
        height={288}
      />
      <div className="flex flex-col gap-2">
        <h3 className="text-h2 text-grey-500 font-bold">No Announcements</h3>
        <p className="text-p2 text-grey-400">
          The people wanna know what you have to say!
        </p>
      </div>
      <Button
        type="button"
        onClick={onCreateClick}
        className="max-w-xs w-full"
      >
        Create Announcement
      </Button>
    </div>
  );
}
