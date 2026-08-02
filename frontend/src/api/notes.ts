import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { useAuthStore } from './authStore';
import {
  createNoteMutation,
  deleteNoteMutation,
  getNotesOptions,
  getNotesQueryKey,
  updateNoteMutation,
  uploadImageMutation,
} from './generated/@tanstack/react-query.gen';

export function useNotes(
  noteChainId: string | null | undefined,
  enabled = true
) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  return useQuery({
    ...getNotesOptions({ path: { note_chain_id: noteChainId ?? '' } }),
    enabled: isAuthenticated && enabled && !!noteChainId,
    placeholderData: [],
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
    },
  });
}

export function useUploadImage() {
  return useMutation({
    ...uploadImageMutation(),
  });
}
