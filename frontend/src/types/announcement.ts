export interface Announcement {
  announcement_id: string;
  user_id: string;
  author_name: string;
  subject: string;
  message: string;
  attachments: string[];
  created_at: string | null;
  updated_at: string | null;
}

export interface AnnouncementCreatePayload {
  user_id: string;
  subject: string;
  message: string;
  attachments?: string[];
}

export interface AnnouncementUpdatePayload {
  subject?: string;
  message?: string;
  attachments?: string[];
}
