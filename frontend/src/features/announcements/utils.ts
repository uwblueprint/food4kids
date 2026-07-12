import { useAuthStore } from '@/api/authStore';
import type { Announcement } from '@/types/announcement';

export const MESSAGE_MAX = 1500;
export const SUBJECT_MAX = 100;
const NEW_BADGE_DAYS = 7;

/** Figma: fixed 544px side panel width. */
export const PANEL_WIDTH = 544;

/** Mobile & tablet: bottom sheet height — 6/7 of the viewport. */
export const SHEET_HEIGHT = 'calc(100dvh * 6 / 7)';

export const SHEET_HEIGHT_CSS_VAR = '--announcements-sheet-height';

export function sheetHeightStyle(): Record<string, string> {
  return { [SHEET_HEIGHT_CSS_VAR]: SHEET_HEIGHT };
}

/** Bottom sheet layout for announcements panel (mobile + tablet). */
export const SHEET_PANEL_LAYOUT =
  'bg-grey-100 inset-x-0 top-auto right-auto bottom-0 h-[var(--announcements-sheet-height)] w-full max-w-none translate-none rounded-none rounded-t-2xl';

/** Desktop: right side panel. */
export const DESKTOP_PANEL_LAYOUT =
  'desktop:inset-x-auto desktop:bottom-auto desktop:top-0 desktop:right-0 desktop:left-auto desktop:bg-grey-150 desktop:h-dvh desktop:w-[var(--announcements-panel-width)] desktop:max-w-[var(--announcements-panel-width)] desktop:rounded-none desktop:rounded-l-2xl';

/** Bottom sheet layout for modal content (mobile + tablet). */
export const SHEET_MODAL_LAYOUT =
  'top-auto right-0 bottom-0 left-0 h-[var(--announcements-sheet-height)] max-h-[var(--announcements-sheet-height)] w-full max-w-none translate-x-0 translate-y-0 rounded-none rounded-t-2xl flex flex-col';

/** Desktop: centered dialog (content height, capped so long lists don't fill the viewport). */
export const DESKTOP_MODAL_LAYOUT =
  'desktop:top-1/2 desktop:right-auto desktop:bottom-auto desktop:left-1/2 desktop:h-auto desktop:max-h-[min(640px,85vh)] desktop:w-full desktop:max-w-[560px] desktop:-translate-x-1/2 desktop:-translate-y-1/2 desktop:rounded-2xl';

export function roleFromStoredToken(): 'admin' | 'driver' {
  const role = useAuthStore.getState().user?.role;
  return role === 'admin' ? 'admin' : 'driver';
}

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
