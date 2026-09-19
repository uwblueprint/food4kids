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
    driverId: string | null; // Populated if they are a driver
    adminId: string | null; // Populated if they are an admin
  } | null;
  isAuthenticated: boolean;
  isRestoringSession: boolean;
  /**
   * The session ended on its own rather than by logging out — the token was
   * expired, or revoked out from under us. Distinguishes "we signed you out"
   * from "you were never signed in", which the login page needs in order to
   * explain itself to someone who was working a moment ago.
   */
  sessionExpired: boolean;
  rememberMe: boolean;
  setAuth: (authData: AuthResponse) => void;
  setAuthFromRegister: (registerData: DriverRegisterResponse) => void;
  clearAuth: () => void;
  /** Sign out because the server rejected our token. See `axiosClient`. */
  expireSession: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  user: null,
  isAuthenticated: false,
  isRestoringSession: true,
  sessionExpired: false,
  rememberMe: false,

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
        role: authData.role,
        driverId: authData.driver_id ?? null,
        adminId: authData.admin_id ?? null,
      },
      isAuthenticated: true,
      isRestoringSession: false,
      // Whatever ended the last session, this one supersedes it.
      sessionExpired: false,
      rememberMe: authData.remember_me,
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
        adminId: registerData.auth.admin_id ?? null,
      },
      isAuthenticated: true,
      isRestoringSession: false,
      sessionExpired: false,
      rememberMe: registerData.auth.remember_me,
    }),

  clearAuth: () =>
    set({
      accessToken: null,
      user: null,
      isAuthenticated: false,
      isRestoringSession: false,
      sessionExpired: false,
      rememberMe: false,
    }),

  expireSession: () =>
    set({
      accessToken: null,
      user: null,
      isAuthenticated: false,
      isRestoringSession: false,
      sessionExpired: true,
      rememberMe: false,
    }),
}));
