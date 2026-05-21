import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  createAnnouncementMutation,
  deleteAnnouncementMutation,
  getAnnouncementsOptions,
  getAnnouncementsQueryKey,
} from './generated/@tanstack/react-query.gen';

/**
 * Demo hooks built on the generated OpenAPI client.
 *
 * Compare to addresses.ts / route-groups.ts (hand-written): no URL strings, no
 * manual response types, no separately maintained query key shape.
 */

export function useAnnouncements() {
  return useQuery(getAnnouncementsOptions());
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

export function useDeleteAnnouncement() {
  const queryClient = useQueryClient();
  return useMutation({
    ...deleteAnnouncementMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: getAnnouncementsQueryKey() });
    },
  });
}
