import { useMutation, useQuery } from '@tanstack/react-query';

import { useAuthStore } from './authStore';
import {
  completeDriverRegistration,
  forgotPassword,
  getDrivers,
  type ForgotPasswordRequest,
  login,
  type LoginRequest,
  refresh,
  updatePassword,
  type UpdatePasswordRequest,
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
    onError: (error) => {
      console.error('Registration error:', error);
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
          console.error('Failed to fetch driver info:', error);
        }
      }

      // Update auth again with driverId if we found it
      if (driverId) {
        setAuth(data, driverId);
      }
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
            console.error('Failed to fetch driver info during refresh:', error);
          }
        }

        // Update auth again with driverId if we found it
        if (driverId) {
          setAuth(data, driverId);
        }

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
