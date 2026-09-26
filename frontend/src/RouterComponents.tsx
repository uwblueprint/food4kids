import { Navigate, Outlet } from 'react-router-dom';

import { useAuthStore } from './api/authStore';
import { homePathForRole } from './common/utils';
import { AuthProvider } from './contexts/AuthProvider';

// Moved into a separate file to satisfy linting rules

export function RootRedirect() {
  const user = useAuthStore((state) => state.user);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Navigate to={homePathForRole(user?.role)} replace />;
}

export function RootLayout() {
  return (
    <AuthProvider>
      <Outlet />
    </AuthProvider>
  );
}
