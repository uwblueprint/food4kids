import type { Announcement } from '@/types/announcement';
import type { UserRole } from '@/contexts/AuthContext';

const SUBJECT_MAX = 100;
const MESSAGE_MAX = 1500;
const NEW_BADGE_DAYS = 7;

export { SUBJECT_MAX, MESSAGE_MAX };

export function formatAnnouncementDate(isoDate: string | null): string {
  if (!isoDate) return '';
  const date = new Date(isoDate);
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

export function isAnnouncementNew(createdAt: string | null): boolean {
  if (!createdAt) return false;
  const created = new Date(createdAt).getTime();
  const cutoff = Date.now() - NEW_BADGE_DAYS * 24 * 60 * 60 * 1000;
  return created >= cutoff;
}

export function canManageAnnouncement(
  announcement: Announcement,
  currentUserId: string,
  role: UserRole
): boolean {
  if (role === 'admin') return true;
  return announcement.user_id === currentUserId;
}

export function authorDisplayLabel(
  announcement: Announcement,
  currentUserId: string
): string {
  if (announcement.user_id === currentUserId) {
    return `${announcement.author_name || 'You'} (You)`;
  }
  return announcement.author_name || 'Unknown';
}
