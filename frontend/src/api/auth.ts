import { useMutation } from '@tanstack/react-query';

import { login, type LoginRequest } from './generated';
import { useAuthStore } from './authStore';

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
