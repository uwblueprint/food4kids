import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
} from 'react';

export type UserRole = 'admin' | 'driver';

export interface CurrentUser {
  userId: string;
  name: string;
  role: UserRole;
}

const STORAGE_KEY = 'f4k_auth';

interface AuthContextValue {
  user: CurrentUser;
  setUser: (user: CurrentUser) => void;
  clearUser: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function readStoredUser(): CurrentUser | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as CurrentUser;
  } catch {
    return null;
  }
}

function getDefaultUser(): CurrentUser {
  const role =
    (import.meta.env.VITE_DEV_USER_ROLE as UserRole | undefined) ?? 'admin';
  return {
    userId: import.meta.env.VITE_DEV_USER_ID ?? '',
    name: import.meta.env.VITE_DEV_USER_NAME ?? 'Dev User',
    role,
  };
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUserState] = useState<CurrentUser>(
    () => readStoredUser() ?? getDefaultUser()
  );

  const setUser = useCallback((next: CurrentUser) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    setUserState(next);
  }, []);

  const clearUser = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setUserState(getDefaultUser());
  }, []);

  const value = useMemo(
    () => ({ user, setUser, clearUser }),
    [user, setUser, clearUser]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}

/** Call after login to persist user for announcements and other features. */
export function persistAuthUser(user: CurrentUser): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
}
