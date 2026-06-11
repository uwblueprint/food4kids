export interface Announcement {
  announcement_id: string;
  user_id: string;
  author_name: string;
<<<<<<< HEAD
<<<<<<< HEAD
  author_role: string;
=======
>>>>>>> fa70cf5 (add board and crud functionality)
=======
  author_role: string;
>>>>>>> b56351b (add bulk edit modal)
  subject: string;
  message: string;
  attachments: string[];
  created_at: string | null;
  updated_at: string | null;
}

export interface AnnouncementCreatePayload {
<<<<<<< HEAD
=======
  user_id: string;
>>>>>>> fa70cf5 (add board and crud functionality)
  subject: string;
  message: string;
  attachments?: string[];
}

export interface AnnouncementUpdatePayload {
  subject?: string;
  message?: string;
  attachments?: string[];
}
