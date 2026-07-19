import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { useAuthStore } from './authStore';
import {
  createAnnouncementMutation,
  deleteAnnouncementMutation,
  getAnnouncementsOptions,
  getAnnouncementsQueryKey,
  markAnnouncementsAsReadMutation,
  sendAnnouncementEmailMutation,
  updateAnnouncementMutation,
} from './generated/@tanstack/react-query.gen';
import type { AnnouncementRead } from './generated/types.gen';

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

export function useMarkAnnouncementsAsRead() {
  const queryClient = useQueryClient();
  return useMutation({
    ...markAnnouncementsAsReadMutation(),
    onMutate: async () => {
      const queryKey = getAnnouncementsQueryKey();
      await queryClient.cancelQueries({ queryKey });
      const previous = queryClient.getQueryData<AnnouncementRead[]>(queryKey);
      queryClient.setQueryData<AnnouncementRead[]>(queryKey, (current) =>
        current?.map((announcement) => ({ ...announcement, is_read: true }))
      );
      return { previous };
    },
    onError: (_error, _variables, context) => {
      if (context?.previous) {
        queryClient.setQueryData(getAnnouncementsQueryKey(), context.previous);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: getAnnouncementsQueryKey() });
    },
  });
}
