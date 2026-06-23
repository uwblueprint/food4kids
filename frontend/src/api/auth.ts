import { useMutation } from '@tanstack/react-query';

import { login, type LoginRequest } from './generated';

export function useLogin() {
  return useMutation({
    mutationFn: async (credentials: LoginRequest) => {
      const { data } = await login({
        body: credentials,
        throwOnError: true,
      });
      return data;
    },
    onSuccess: (data) => {
      console.log('Login success:', data);
    },
    onError: (error) => {
      console.error('Login error:', error);
    },
  });
}
