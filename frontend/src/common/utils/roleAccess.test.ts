import { describe, expect, it } from 'vitest';

import {
  HOME_PATH,
  homePathForRole,
  isRole,
  resolveRoleAccess,
  type Role,
  ROLES,
} from './roleAccess';

/** Values the auth store could plausibly hold that are not a known role. */
const NON_ROLES = [
  null,
  undefined,
  '',
  'Admin',
  'ADMIN',
  'admin ',
  ' driver',
  'Driver',
  'superadmin',
  'admins',
  'driver,admin',
  'volunteer',
  'null',
  'undefined',
] as const;

describe('isRole', () => {
  it.each(ROLES)('accepts %s', (role) => {
    expect(isRole(role)).toBe(true);
  });

  it.each(NON_ROLES)('rejects %o', (value) => {
    expect(isRole(value)).toBe(false);
  });
});

describe('resolveRoleAccess', () => {
  it.each(ROLES)('lets %s into their own section', (role) => {
    expect(resolveRoleAccess(role, role)).toEqual({ allowed: true });
  });

  it('sends a driver who reaches an admin route to the driver home', () => {
    expect(resolveRoleAccess('driver', 'admin')).toEqual({
      allowed: false,
      redirectTo: '/driver/home',
    });
  });

  it('sends an admin who reaches a driver route to the admin home', () => {
    expect(resolveRoleAccess('admin', 'driver')).toEqual({
      allowed: false,
      redirectTo: '/admin/home',
    });
  });

  // The full cross product, so a third role added later cannot quietly skip a
  // pairing: every mismatch redirects to the caller's own home, never the
  // section they were denied.
  it.each(ROLES.flatMap((role) => ROLES.map((required) => [role, required])))(
    'role=%s requiredRole=%s',
    (role, requiredRole) => {
      const access = resolveRoleAccess(role, requiredRole);
      if (role === requiredRole) {
        expect(access).toEqual({ allowed: true });
      } else {
        expect(access).toEqual({
          allowed: false,
          redirectTo: HOME_PATH[role as Role],
        });
      }
    }
  );

  // Fails closed: `role` is a free-form string on the backend, so an
  // unrecognised value must not be handed either app by default.
  describe.each(ROLES)('requiredRole=%s', (requiredRole) => {
    it.each(NON_ROLES)('denies %o and sends it to /login', (value) => {
      expect(resolveRoleAccess(value, requiredRole)).toEqual({
        allowed: false,
        redirectTo: '/login',
      });
    });
  });
});

describe('homePathForRole', () => {
  it.each(ROLES)('maps %s to its own home', (role) => {
    expect(homePathForRole(role)).toBe(HOME_PATH[role]);
  });

  it.each(NON_ROLES)('maps %o to /login', (value) => {
    expect(homePathForRole(value)).toBe('/login');
  });

  it('never maps an unknown role into an app section', () => {
    for (const value of NON_ROLES) {
      expect(homePathForRole(value)).not.toMatch(/^\/(admin|driver)\b/);
    }
  });
});
