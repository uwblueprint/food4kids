import React, { useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';

import { useLogout, useRefresh } from '@/api/auth';
import { useAuthStore } from '@/api/authStore';
import { Button } from '@/common/components/Button';

import { useInactivityTimeout } from './useInactivityTimeout';

const PUBLIC_ROUTES = [
  '/login',
  '/create-password',
  '/forgot-password',
  '/404',
  '/403',
  '/503',
  '/error',
  '/style-guide',
];

/**
 * Every protected page starts with a `/auth/refresh` call to find out who is
 * signed in. Render nothing for this long, so a quick refresh never flashes a
 * "Restoring your session..." screen.
 */
export const RESTORE_GRACE_MS = 300;

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const { isError, isFetching, refetch } = useRefresh();

  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const isRestoringSession = useAuthStore((state) => state.isRestoringSession);
  const rememberMe = useAuthStore((state) => state.rememberMe);

  const [graceElapsed, setGraceElapsed] = useState(false);
  useEffect(() => {
    const timer = setTimeout(() => setGraceElapsed(true), RESTORE_GRACE_MS);
    return () => clearTimeout(timer);
  }, []);

  const location = useLocation();
  const isPublicRoute = PUBLIC_ROUTES.some((route) =>
    location.pathname.startsWith(route)
  );

  const logoutMutation = useLogout();

  useInactivityTimeout({
    onTimeout: () => {
      logoutMutation.mutate();
    },
    enabled: isAuthenticated && !rememberMe && !isPublicRoute,
  });

  if (isPublicRoute) {
    return <>{children}</>;
  }

  if (isRestoringSession) {
    if (!graceElapsed) {
      return null;
    }

    // A refused refresh clears the store, so an error while still restoring
    // means the request never got an answer. Offer to ask again.
    if (isError && !isFetching) {
      return (
        <div className="flex h-screen w-screen flex-col items-center justify-center gap-4 bg-gray-50">
          <span className="text-sm font-medium text-gray-500">
            Couldn&apos;t reach the server to restore your session.
          </span>
          <Button variant="primary" onClick={() => void refetch()}>
            Try again
          </Button>
        </div>
      );
    }

    return (
      <div className="flex h-screen w-screen items-center justify-center bg-gray-50">
        <span className="text-sm font-medium text-gray-500">
          Restoring your session...
        </span>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}
