import { useQuery } from '@tanstack/react-query';

import axiosClient from '@/lib/axiosClient';

export interface CurrentUser {
  user_id: string;
  name: string;
  email: string;
  auth_id: string | null;
  role: string;
}

const CURRENT_USER_KEY = ['currentUser'] as const;

async function fetchCurrentUser(): Promise<CurrentUser> {
  const response = await axiosClient.get<CurrentUser>('/auth/me');
  return response.data;
}

export function useCurrentUser() {
  return useQuery({
    queryKey: CURRENT_USER_KEY,
    queryFn: fetchCurrentUser,
    retry: false,
  });
}
