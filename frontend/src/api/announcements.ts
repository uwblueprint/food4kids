import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import axiosClient from '@/lib/axiosClient';
import type {
  Announcement,
  AnnouncementCreatePayload,
  AnnouncementUpdatePayload,
} from '@/types/announcement';

const ANNOUNCEMENTS_KEY = ['announcements'] as const;

async function fetchAnnouncements(): Promise<Announcement[]> {
  const response = await axiosClient.get<Announcement[]>('/announcements/');
  return response.data;
}

async function createAnnouncement(
  payload: AnnouncementCreatePayload
): Promise<Announcement> {
  const response = await axiosClient.post<Announcement>(
    '/announcements/',
    payload
  );
  return response.data;
}

async function updateAnnouncement(
  announcementId: string,
  payload: AnnouncementUpdatePayload
): Promise<Announcement> {
  const response = await axiosClient.put<Announcement>(
    `/announcements/${announcementId}`,
    payload
  );
  return response.data;
}

async function deleteAnnouncement(announcementId: string): Promise<void> {
  await axiosClient.delete(`/announcements/${announcementId}`);
}

async function sendAnnouncementEmail(
  announcementId: string
): Promise<{ sent: number; failed: number }> {
  const response = await axiosClient.post<{ sent: number; failed: number }>(
    `/announcements/${announcementId}/email`
  );
  return response.data;
}

export function useAnnouncements() {
  return useQuery({
    queryKey: ANNOUNCEMENTS_KEY,
    queryFn: fetchAnnouncements,
    enabled: localStorage.getItem('token') !== null,
    placeholderData: [],
  });
}

export function useCreateAnnouncement() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createAnnouncement,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ANNOUNCEMENTS_KEY });
    },
  });
}

export function useUpdateAnnouncement() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      announcementId,
      payload,
    }: {
      announcementId: string;
      payload: AnnouncementUpdatePayload;
    }) => updateAnnouncement(announcementId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ANNOUNCEMENTS_KEY });
    },
  });
}

export function useDeleteAnnouncement() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteAnnouncement,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ANNOUNCEMENTS_KEY });
    },
  });
}

export function useSendAnnouncementEmail() {
  return useMutation({
    mutationFn: sendAnnouncementEmail,
  });
}
