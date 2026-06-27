import { create } from 'zustand';
import { type AuthResponse, type DriverRegisterResponse } from './generated';

interface AuthState {
  accessToken: string | null;
  user: {
    id: string;
    firstName: string;
    lastName: string;
    email: string;
    fullName: string;
    role: string;
    driverId?: string;   // Populated if they are a driver
  } | null;
  isAuthenticated: boolean;
  setAuth: (authData: AuthResponse) => void;
  setAuthFromRegister: (registerData: DriverRegisterResponse) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  user: null,
  isAuthenticated: false,

  // Called after a successful Login
  setAuth: (authData) =>
    set({
      accessToken: authData.access_token,
      user: {
        id: authData.id,
        firstName: authData.first_name,
        lastName: authData.last_name,
        email: authData.email,
        fullName: authData.full_name,
        role: authData.role
      },
      isAuthenticated: true,
    }),

  // Called after a successful Registration
  setAuthFromRegister: (registerData) =>
    set({
      accessToken: registerData.auth.access_token,
      user: {
        id: registerData.auth.id,
        firstName: registerData.auth.first_name,
        lastName: registerData.auth.last_name,
        email: registerData.auth.email,
        fullName: registerData.auth.full_name,
        role: registerData.driver.role,
        driverId: registerData.driver.driver_id,
      },
      isAuthenticated: true,
    }),

  clearAuth: () => set({ accessToken: null, user: null, isAuthenticated: false }),
}));
