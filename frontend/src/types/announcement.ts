export interface Announcement {
  announcement_id: string;
  user_id: string;
  author_name: string;
  author_role: string;
  subject: string;
  message: string;
  attachments: string[];
  created_at: string | null;
  updated_at: string | null;
  is_read?: boolean | null;
}

export interface AnnouncementCreatePayload {
  subject: string;
  message: string;
  attachments?: string[];
}

export interface AnnouncementUpdatePayload {
  subject?: string;
  message?: string;
  attachments?: string[];
}
