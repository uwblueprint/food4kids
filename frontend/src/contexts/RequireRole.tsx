import { Navigate, Outlet } from 'react-router-dom';

import { useAuthStore } from '@/api/authStore';
import { resolveRoleAccess, type Role } from '@/common/utils';

/**
 * Route guard for a role-owned section of the app. Wrap the `/admin` and
 * `/driver` branches so neither role can reach the other's pages by typing the
 * URL. `AuthProvider` has already settled the session and bounced anonymous
 * callers by the time this renders, so the only question left is the role.
 *
 * A user in the wrong app is redirected to their own home rather than shown a
 * 403 — see `resolveRoleAccess` for why.
 */
export function RequireRole({ requiredRole }: { requiredRole: Role }) {
  // Named `requiredRole`, not `role`: jsx-a11y reads a `role` prop on any JSX
  // element as an ARIA role and rejects "admin"/"driver".
  const userRole = useAuthStore((state) => state.user?.role);

  const access = resolveRoleAccess(userRole, requiredRole);
  if (!access.allowed) {
    return <Navigate to={access.redirectTo} replace />;
  }

  return <Outlet />;
}
