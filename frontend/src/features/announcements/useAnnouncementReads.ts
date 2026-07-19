import { useCallback } from 'react';

import { useMarkAnnouncementsAsRead } from '@/api/announcements';

export function useAnnouncementReads() {
  const { mutate, isPending } = useMarkAnnouncementsAsRead();

  const markBoardAsRead = useCallback(() => {
    if (isPending) return;
    mutate({});
  }, [mutate, isPending]);

  return { markBoardAsRead, isMarkingRead: isPending };
}
