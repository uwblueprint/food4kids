import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  createAnnouncementMutation,
  deleteAnnouncementMutation,
  getAnnouncementsOptions,
  getAnnouncementsQueryKey,
  sendAnnouncementEmailMutation,
  updateAnnouncementMutation,
} from './generated/@tanstack/react-query.gen';

export function useAnnouncements() {
  return useQuery({
    ...getAnnouncementsOptions(),
    enabled: localStorage.getItem('token') !== null,
    placeholderData: [],
  });
}

export function useCreateAnnouncement() {
  const queryClient = useQueryClient();
  return useMutation({
    ...createAnnouncementMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: getAnnouncementsQueryKey() });
    },
  });
}

export function useUpdateAnnouncement() {
  const queryClient = useQueryClient();
  return useMutation({
    ...updateAnnouncementMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: getAnnouncementsQueryKey() });
    },
  });
}

export function useDeleteAnnouncement() {
  const queryClient = useQueryClient();
  return useMutation({
    ...deleteAnnouncementMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: getAnnouncementsQueryKey() });
    },
  });
}

export function useSendAnnouncementEmail() {
  return useMutation({
    ...sendAnnouncementEmailMutation(),
  });
}
