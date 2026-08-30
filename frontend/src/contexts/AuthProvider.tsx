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
 * How long a session restore may run before it says anything about itself.
 *
 * The access token is held in memory only, so every load of a protected route
 * — including a logged-out visit to `/` on the way to the login page — waits on
 * a `/auth/refresh` round trip before anyone knows who is here. A warm one
 * lands well inside this window and the visitor sees nothing at all; only a
 * genuinely slow one is worth explaining.
 */
export const RESTORE_GRACE_MS = 300;

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const {
    isError: restoreFailed,
    isFetching: restoreInFlight,
    refetch: retryRestore,
  } = useRefresh();

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
    // Inside the grace window: say nothing rather than flash a gate that the
    // page itself is about to replace.
    if (!graceElapsed) {
      return null;
    }

    // A refusal ends the restore by clearing the store, so a failure that is
    // still restoring never got an answer. The session is intact but unknown,
    // and the only thing left to do is ask again.
    if (restoreFailed && !restoreInFlight) {
      return (
        <div className="flex h-screen w-screen flex-col items-center justify-center gap-4 bg-gray-50">
          <span className="text-sm font-medium text-gray-500">
            Couldn&apos;t reach the server to restore your session.
          </span>
          <Button variant="primary" onClick={() => void retryRestore()}>
            Try again
          </Button>
        </div>
      );
    }

    return (
      <div className="flex h-screen w-screen items-center justify-center bg-gray-50">
        <div className="flex flex-col items-center gap-2">
          <span className="text-sm font-medium text-gray-500">
            Restoring your session...
          </span>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}
