import { useMutation, useQuery } from '@tanstack/react-query';

import { useAuthStore } from './authStore';
import { login, type LoginRequest, refresh } from './generated';

export function useLogin() {
  const setAuth = useAuthStore((state) => state.setAuth);

  return useMutation({
    mutationFn: async (credentials: LoginRequest) => {
      const { data } = await login({
        body: credentials,
        throwOnError: true,
      });
      return data;
    },
    onSuccess: (data) => {
      setAuth(data);
    },
    onError: (error) => {
      console.error('Login error:', error);
    },
  });
}

export function useRefresh() {
  const setAuth = useAuthStore((state) => state.setAuth);
  const clearAuth = useAuthStore((state) => state.clearAuth);

  return useQuery({
    queryKey: ['session-refresh'],
    queryFn: async () => {
      try {
        const { data } = await refresh({
          throwOnError: true,
        });

        setAuth(data);
        return data;
      } catch (error) {
        console.error('Session auto-refresh failed:', error);
        clearAuth();
        throw error;
      }
    },
    retry: false,
    refetchOnWindowFocus: false,
    staleTime: Infinity,
  });
}
