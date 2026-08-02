import type { NoteRead } from '@/api/generated/types.gen';

export const NOTE_MESSAGE_MAX = 300;
export const NOTE_IMAGE_MAX = 3;
export const NOTE_IMAGE_MAX_BYTES = 5 * 1024 * 1024;
export const NOTE_IMAGE_ACCEPT = 'image/png,image/jpeg,image/gif';

export function formatNoteDate(isoDate: string | null | undefined): string {
  if (!isoDate) return '';
  return new Date(isoDate).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  });
}

export function noteAuthorLabel(
  note: NoteRead,
  currentUserId: string,
  currentUserName: string
): string {
  if (note.is_system) return 'System';
  if (note.user_id && note.user_id === currentUserId) {
    return currentUserName.trim() || 'You';
  }
  return 'Unknown';
}

export function canManageNote(
  note: NoteRead,
  currentUserId: string,
  role: string
): boolean {
  if (note.is_system) return false;
  if (role === 'admin') return true;
  return !!note.user_id && note.user_id === currentUserId;
}

export function formatPhoneDisplay(phone: string): string {
  const digits = phone.replace(/\D/g, '');
  if (digits.length === 10) {
    return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6)}`;
  }
  if (digits.length === 11 && digits.startsWith('1')) {
    return `(${digits.slice(1, 4)}) ${digits.slice(4, 7)}-${digits.slice(7)}`;
  }
  return phone;
}

export function telHref(phone: string): string {
  const digits = phone.replace(/\D/g, '');
  return digits ? `tel:${digits}` : `tel:${phone}`;
}

export function isAllowedNoteImage(file: File): boolean {
  return ['image/png', 'image/jpeg', 'image/gif'].includes(file.type);
}
