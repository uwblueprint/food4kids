import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { useAuthStore } from './authStore';
import {
  createAnnouncementMutation,
  deleteAnnouncementMutation,
  getAnnouncementsOptions,
  getAnnouncementsQueryKey,
  sendAnnouncementEmailMutation,
  updateAnnouncementMutation,
} from './generated/@tanstack/react-query.gen';

export function useAnnouncements() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  return useQuery({
    ...getAnnouncementsOptions(),
    enabled: isAuthenticated,
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
