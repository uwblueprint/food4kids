import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { refreshSession } from '@/lib/axiosClient';

import { useAuthStore } from './authStore';
import {
  completeDriverRegistration,
  forgotPassword,
  type ForgotPasswordRequest,
  login,
  type LoginRequest,
  logout,
  updatePassword,
  updatePasswordAuthed,
  type UpdatePasswordRequest,
  type UpdatePasswordAuthedRequest,
  type UserFinalize,
  validateResetToken,
  type ValidateResetTokenRequest,
} from './generated';

export function useRegisterDriver() {
  const setAuthFromRegister = useAuthStore(
    (state) => state.setAuthFromRegister
  );

  return useMutation({
    mutationFn: async (payload: UserFinalize) => {
      const { data } = await completeDriverRegistration({
        body: payload,
        throwOnError: true,
      });
      return data;
    },
    onSuccess: (data) => {
      setAuthFromRegister(data);
    },
  });
}

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
  });
}

export function useRefresh() {
  const clearAuth = useAuthStore((state) => state.clearAuth);

  return useQuery({
    queryKey: ['session-refresh'],
    queryFn: async () => {
      try {
        // The same exchange the 401 handler runs mid-session, so a reload and a
        // token that aged out under an open tab restore the session identically.
        return await refreshSession();
      } catch (error) {
        clearAuth();
        throw error;
      }
    },
    retry: false,
    refetchOnWindowFocus: false,
    staleTime: Infinity,
  });
}

export function useForgotPassword() {
  return useMutation({
    mutationFn: async (payload: ForgotPasswordRequest) => {
      const { data } = await forgotPassword({
        body: payload,
        throwOnError: true,
      });
      return data;
    },
  });
}

export function useValidateResetToken(payload: ValidateResetTokenRequest) {
  return useQuery({
    queryKey: ['validate-reset-token', payload],
    queryFn: async () => {
      const { data } = await validateResetToken({
        body: payload,
        throwOnError: true,
      });
      return data;
    },
    retry: false,
    refetchOnWindowFocus: false,
  });
}

export function useUpdatePassword() {
  return useMutation({
    mutationFn: async (payload: UpdatePasswordRequest) => {
      const { data } = await updatePassword({
        body: payload,
        throwOnError: true,
      });
      return data;
    },
  });
}

export function useUpdatePasswordAuthed() {
  const setAuth = useAuthStore((state) => state.setAuth);

  return useMutation({
    mutationFn: async (payload: UpdatePasswordAuthedRequest) => {
      const { data } = await updatePasswordAuthed({
        body: payload,
        throwOnError: true,
      });
      return data;
    },
    onSuccess: async (data) => {
      // First set auth with the access token so axios client is configured
      setAuth(data, undefined);

      let driverId: string | undefined;

      // If user is a driver, fetch their driver_id from the drivers endpoint
      if (data.role === 'driver') {
        try {
          const { data: drivers } = await getDrivers({
            query: { email: data.email },
            throwOnError: true,
          });
          if (drivers && drivers.length > 0) {
            driverId = drivers[0].driver_id;
          }
        } catch (error) {
          console.error('Failed to fetch driver info during password update:', error);
        }
      }

      // Update auth again with driverId if we found it
      if (driverId) {
        setAuth(data, driverId);
      }
    },
    onError: (error) => {
      console.error('Update password error:', error);
    },
  });
}

export function useLogout() {
  const clearAuth = useAuthStore((state) => state.clearAuth);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      await logout({
        throwOnError: true,
      });
    },
    onSettled: () => {
      clearAuth();
      queryClient.clear();
    },
  });
}
