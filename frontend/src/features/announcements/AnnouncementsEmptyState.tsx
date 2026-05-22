import boyAnnouncing from '@/assets/illustrations/boy-announcing.png';
import { Button } from '@/common/components';

interface AnnouncementsEmptyStateProps {
  onCreateClick: () => void;
}

export function AnnouncementsEmptyState({
  onCreateClick,
}: AnnouncementsEmptyStateProps) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-6 px-6 py-12 text-center">
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
      <Button type="button" onClick={onCreateClick} className="w-full max-w-xs">
        Create Announcement
      </Button>
    </div>
  );
}
