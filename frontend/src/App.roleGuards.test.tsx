// @vitest-environment happy-dom
/**
 * Role separation at the router level: a driver must not reach the admin app
 * and an admin must not reach the driver app, whichever URL they type.
 *
 * This drives the real route table in App.tsx — the guard being *wired onto
 * both branches* is the thing that regresses, not the decision function, which
 * is unit-tested in common/utils/roleAccess.test.ts. Only the layouts and page
 * components are stubbed, so no page needs a query client or an API.
 */
import { cleanup, render, screen } from '@testing-library/react';
import type { ReactElement } from 'react';
import { MemoryRouter, Outlet, useLocation } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useAuthStore } from './api/authStore';

const stub = (name: string) => () => <div data-testid={name} />;

const shell = (name: string) => () => (
  <div data-testid={name}>
    <Outlet />
  </div>
);

vi.mock('./layouts', () => ({
  AdminLayout: shell('admin-layout'),
  DriverLayout: shell('driver-layout'),
}));

vi.mock('./pages/admin', () => ({
  AdminDriversPage: stub('admin-drivers'),
  AdminHomePage: stub('admin-home'),
  AdminRoutesGenerationLayout: shell('admin-generation'),
  AdminRoutesPage: stub('admin-routes'),
  AdminSettingsPage: stub('admin-settings'),
  ConfigureStep: stub('admin-configure'),
  GenerateStep: stub('admin-generate'),
  ImportStep: stub('admin-import'),
  ReviewStep: stub('admin-review'),
  ValidateStep: stub('admin-validate'),
}));

vi.mock('./pages/driver', () => ({
  DriverHomePage: stub('driver-home'),
  IndividualRoutePage: stub('driver-route'),
}));

vi.mock('./pages/auth', () => ({
  CreatePassword: stub('create-password'),
  ForgotPassword: stub('forgot-password'),
  LoginPage: stub('login'),
  ResetPassword: stub('reset-password'),
}));

vi.mock('./pages/StyleGuide', () => ({ StyleGuidePage: stub('style-guide') }));
vi.mock('./pages/TestImageUpload', () => ({
  TestImageUpload: stub('test-image-upload'),
}));

// Imported after the mocks so App picks up the stubbed modules.
const { default: App } = await import('./App');

function LocationProbe(): ReactElement {
  const { pathname } = useLocation();
  return <div data-testid="pathname">{pathname}</div>;
}

function signIn(role: string | null) {
  useAuthStore.setState({
    accessToken: 'token',
    isAuthenticated: true,
    isRestoringSession: false,
    user:
      role === null
        ? null
        : {
            id: 'u1',
            firstName: 'Test',
            lastName: 'User',
            email: 'test@example.com',
            fullName: 'Test User',
            role,
            driverId: role === 'driver' ? 'd1' : null,
            adminId: role === 'admin' ? 'a1' : null,
          },
  });
}

/** Render the app at `path` and report where the router settled. */
function visit(path: string): string {
  render(
    <MemoryRouter initialEntries={[path]}>
      <LocationProbe />
      <App />
    </MemoryRouter>
  );
  return screen.getByTestId('pathname').textContent ?? '';
}

const ADMIN_PATHS = [
  '/admin',
  '/admin/home',
  '/admin/drivers',
  '/admin/routes',
  '/admin/routes/generation',
  '/admin/routes/generation/import',
  '/admin/routes/generation/validate',
  '/admin/routes/generation/review',
  '/admin/routes/generation/configure',
  '/admin/routes/generation/generate',
  '/admin/settings',
  '/admin/test-image-upload',
];

const DRIVER_PATHS = [
  '/driver',
  '/driver/home',
  '/driver/route',
  '/driver/route/abc-123',
];

beforeEach(() => {
  useAuthStore.setState(useAuthStore.getInitialState());
});

afterEach(() => {
  cleanup();
});

describe('a driver cannot reach the admin app', () => {
  it.each(ADMIN_PATHS)('%s redirects to /driver/home', (path) => {
    signIn('driver');
    expect(visit(path)).toBe('/driver/home');
    expect(screen.queryByTestId('admin-layout')).toBeNull();
  });
});

describe('an admin cannot reach the driver app', () => {
  it.each(DRIVER_PATHS)('%s redirects to /admin/home', (path) => {
    signIn('admin');
    expect(visit(path)).toBe('/admin/home');
    expect(screen.queryByTestId('driver-layout')).toBeNull();
  });
});

describe('each role still reaches its own app', () => {
  it.each(ADMIN_PATHS)('an admin is served %s', (path) => {
    signIn('admin');
    visit(path);
    expect(screen.getByTestId('admin-layout')).toBeTruthy();
  });

  it.each(DRIVER_PATHS)('a driver is served %s', (path) => {
    signIn('driver');
    visit(path);
    expect(screen.getByTestId('driver-layout')).toBeTruthy();
  });
});

describe('a user with no usable role reaches neither app', () => {
  // AuthProvider bounces anonymous callers before App renders, so these cover
  // the fail-closed path: a session whose role we cannot place.
  it.each([null, 'volunteer', ''])('role %o is sent to /login', (role) => {
    signIn(role);
    for (const path of [...ADMIN_PATHS, ...DRIVER_PATHS]) {
      expect(visit(path)).toBe('/login');
      cleanup();
    }
  });
});

describe('the root redirect follows the role', () => {
  it('sends a driver to the driver home', () => {
    signIn('driver');
    expect(visit('/')).toBe('/driver/home');
  });

  it('sends an admin to the admin home', () => {
    signIn('admin');
    expect(visit('/')).toBe('/admin/home');
  });

  it('sends an unauthenticated visitor to /login', () => {
    expect(visit('/')).toBe('/login');
  });

  it('sends a signed-in user with an unknown role to /login', () => {
    signIn('volunteer');
    expect(visit('/')).toBe('/login');
  });
});
