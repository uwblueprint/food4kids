/**
 * Which of the two apps — admin or driver — a signed-in user belongs to.
 *
 * The backend stores `role` as a free-form string, so the value arriving in the
 * auth store is not guaranteed to be one of these. Everything here fails
 * closed: an unrecognised role is admitted to neither app.
 */
export const ROLES = ['admin', 'driver'] as const;

export type Role = (typeof ROLES)[number];

export function isRole(role: string | null | undefined): role is Role {
  return ROLES.includes(role as Role);
}

/** Where each role's app starts — the landing spot after login or a redirect. */
export const HOME_PATH: Record<Role, string> = {
  admin: '/admin/home',
  driver: '/driver/home',
};

export type RoleAccess =
  | { allowed: true }
  | { allowed: false; redirectTo: string };

/**
 * Whether `role` may enter a section reserved for `requiredRole`, and where to
 * send them if not.
 *
 * A user in the wrong app is sent to their own home rather than shown a 403:
 * the admin shell renders broken tables for a driver, and there is nothing for
 * them to do there either way. A user with no role, or one we do not recognise,
 * goes to /login — guessing a default would hand an unknown role a whole app.
 */
export function resolveRoleAccess(
  role: string | null | undefined,
  requiredRole: Role
): RoleAccess {
  if (!isRole(role)) {
    return { allowed: false, redirectTo: '/login' };
  }
  if (role !== requiredRole) {
    return { allowed: false, redirectTo: HOME_PATH[role] };
  }
  return { allowed: true };
}

/**
 * The path a signed-in user should land on, given only their role. `/login` for
 * a role we cannot place — same fail-closed rule as `resolveRoleAccess`.
 */
export function homePathForRole(role: string | null | undefined): string {
  return isRole(role) ? HOME_PATH[role] : '/login';
}
