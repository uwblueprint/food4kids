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
        alt="No Announcements. The people wanna know what you have to say!"
        className="h-auto w-full max-w-[295px]"
        width={295}
        height={288}
      />
      <Button type="button" onClick={onCreateClick} className="w-full">
        Create Announcement
      </Button>
    </div>
  );
}
