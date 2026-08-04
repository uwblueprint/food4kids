import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';

import { useRefresh, useLogout } from '@/api/auth';
import { useAuthStore } from '@/api/authStore';
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
  '/test-image-upload',
];

export function AuthProvider({ children }: { children: React.ReactNode }) {
  useRefresh();

  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const isRestoringSession = useAuthStore((state) => state.isRestoringSession);
  const rememberMe = useAuthStore((state) => state.rememberMe);

  const location = useLocation();
  const isPublicRoute = PUBLIC_ROUTES.some((route) =>
    location.pathname.startsWith(route)
  );

  const logoutMutation = useLogout();

  useInactivityTimeout({
    onTimeout: () => { logoutMutation.mutate(); },
    enabled: isAuthenticated && !rememberMe && !isPublicRoute,
  });

  if (isPublicRoute) {
    return <>{children}</>;
  }

  if (isRestoringSession) {
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
