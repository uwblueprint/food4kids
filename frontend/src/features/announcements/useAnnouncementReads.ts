import { useCallback, useMemo, useState } from 'react';

const STORAGE_PREFIX = 'f4k_announcement_reads';

function storageKey(userId: string): string {
  return `${STORAGE_PREFIX}:${userId || 'anonymous'}`;
}

function loadReadIds(userId: string): Set<string> {
  try {
    const raw = localStorage.getItem(storageKey(userId));
    if (!raw) return new Set();
    const parsed = JSON.parse(raw) as string[];
    return new Set(parsed);
  } catch {
    return new Set();
  }
}

function persistReadIds(userId: string, ids: Set<string>): void {
  localStorage.setItem(storageKey(userId), JSON.stringify([...ids]));
}

/** Tracks which announcements the current user has opened (for the New badge). */
export function useAnnouncementReads(userId: string) {
  const [readIds, setReadIds] = useState<Set<string>>(() => loadReadIds(userId));

  const markAsRead = useCallback(
    (announcementId: string) => {
      setReadIds((previous) => {
        if (previous.has(announcementId)) return previous;
        const next = new Set(previous);
        next.add(announcementId);
        persistReadIds(userId, next);
        return next;
      });
    },
    [userId]
  );

  const readIdSet = useMemo(() => readIds, [readIds]);

  return { readIds: readIdSet, markAsRead };
}
