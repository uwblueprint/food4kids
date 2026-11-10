import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { useAuthStore } from './authStore';
import {
  createNoteMutation,
  deleteNoteMutation,
  getNotesFeedOptions,
  getNotesFeedQueryKey,
  getNotesOptions,
  getNotesQueryKey,
  markNoteReadMutation,
  updateNoteMutation,
  uploadImageMutation,
} from './generated/@tanstack/react-query.gen';
import type { GetNotesFeedData } from './generated/types.gen';

export function useNotesFeed(
  query: GetNotesFeedData['query'],
  options: { keepPreviousData?: boolean } = {}
) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const userId = useAuthStore((state) => state.user?.id);
  const feedOptions = getNotesFeedOptions({ query });
  return useQuery({
    ...feedOptions,
    queryKey: [{ ...feedOptions.queryKey[0], tags: [userId ?? ''] }],
    enabled: isAuthenticated,
    placeholderData: options.keepPreviousData
      ? (previous, previousQuery) =>
          previousQuery?.queryKey[0].tags?.[0] === (userId ?? '')
            ? previous
            : undefined
      : undefined,
  });
}

export function useMarkNoteRead() {
  const queryClient = useQueryClient();
  return useMutation({
    ...markNoteReadMutation(),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: getNotesFeedQueryKey() }),
  });
}

export function useNotes(
  noteChainId: string | null | undefined,
  enabled = true
) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  return useQuery({
    ...getNotesOptions({ path: { note_chain_id: noteChainId ?? '' } }),
    enabled: isAuthenticated && enabled && !!noteChainId,
  });
}

export function useCreateNote(noteChainId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    ...createNoteMutation(),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: getNotesQueryKey({ path: { note_chain_id: noteChainId } }),
      });
      void queryClient.invalidateQueries({ queryKey: getNotesFeedQueryKey() });
    },
  });
}

export function useUpdateNote(noteChainId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    ...updateNoteMutation(),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: getNotesQueryKey({ path: { note_chain_id: noteChainId } }),
      });
      void queryClient.invalidateQueries({ queryKey: getNotesFeedQueryKey() });
    },
  });
}

export function useDeleteNote(noteChainId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    ...deleteNoteMutation(),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: getNotesQueryKey({ path: { note_chain_id: noteChainId } }),
      });
      void queryClient.invalidateQueries({ queryKey: getNotesFeedQueryKey() });
    },
  });
}

export function useUploadImage() {
  return useMutation({
    ...uploadImageMutation(),
  });
}
