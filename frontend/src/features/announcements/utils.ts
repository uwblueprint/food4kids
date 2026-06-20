import type { Announcement } from '@/types/announcement';

export const MESSAGE_MAX = 1500;
export const SUBJECT_MAX = 100;
const NEW_BADGE_DAYS = 7;

/** Figma: fixed 544px side panel width. */
export const PANEL_WIDTH = 544;

/** Figma: 32px outer padding on the announcements side panel. */
export const PANEL_PADDING_X = 'px-8';
export const PANEL_PADDING_TOP = 'pt-8';
export const PANEL_PADDING_BOTTOM = 'pb-8';
/** 16px vertical gap between header/content/footer sections. */
export const PANEL_SECTION_GAP = 'py-4';
/** 16px gap between announcement cards. */
export const PANEL_CARD_GAP = 'gap-4';

export function announcementDateLine(announcement: Announcement): string {
  const posted = formatAnnouncementDate(announcement.created_at);
  if (!isAnnouncementEdited(announcement)) {
    return posted;
  }
  const edited = formatAnnouncementDate(announcement.updated_at);
  if (!posted) return `Edited ${edited}`;
  return `Posted ${posted} • Edited ${edited}`;
}

export function authorColorClass(authorRole: string): string {
  return authorRole === 'admin' ? 'text-blue-300' : 'text-grey-400';
}

export function authorDisplayName(
  announcement: Announcement,
  currentUserId: string
): string {
  const name = announcement.author_name || 'Unknown';
  if (announcement.user_id === currentUserId) {
    return `${name} (You)`;
  }
  return name;
}

export function canManageAnnouncement(
  announcement: Announcement,
  currentUserId: string,
  role: 'admin' | 'driver'
): boolean {
  if (role === 'admin') return true;
  return announcement.user_id === currentUserId;
}

export function formatAnnouncementDate(isoDate: string | null): string {
  if (!isoDate) return '';
  const date = new Date(isoDate);
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

export function isAnnouncementEdited(announcement: Announcement): boolean {
  if (!announcement.created_at || !announcement.updated_at) return false;
  const created = new Date(announcement.created_at).getTime();
  const updated = new Date(announcement.updated_at).getTime();
  return updated - created > 1000;
}

/** New = posted within 7 days and not yet opened by the current user. */
export function isAnnouncementNew(
  announcement: Announcement,
  readIds: Set<string>
): boolean {
  if (!announcement.created_at) return false;
  if (readIds.has(announcement.announcement_id)) return false;
  const created = new Date(announcement.created_at).getTime();
  const cutoff = Date.now() - NEW_BADGE_DAYS * 24 * 60 * 60 * 1000;
  return created >= cutoff;
}
