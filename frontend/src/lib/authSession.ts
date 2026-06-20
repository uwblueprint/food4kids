interface LoginResponse {
  access_token: string;
  id: string;
  name: string;
  email: string;
}

export interface AuthSession {
  userId: string;
  role: 'admin' | 'driver';
  email: string;
  name: string;
}

let accessToken: string | null = null;
let session: AuthSession | null = null;

function decodeJwtPayload(token: string): Record<string, unknown> | null {
  try {
    const payload = token.split('.')[1];
    if (!payload) return null;
    return JSON.parse(
      atob(payload.replace(/-/g, '+').replace(/_/g, '/'))
    ) as Record<string, unknown>;
  } catch {
    return null;
  }
}

function roleFromToken(token: string): 'admin' | 'driver' {
  const role = decodeJwtPayload(token)?.role;
  return role === 'admin' ? 'admin' : 'driver';
}

function isTokenExpired(token: string): boolean {
  const exp = decodeJwtPayload(token)?.exp;
  if (typeof exp !== 'number') return true;
  return exp * 1000 <= Date.now() + 60_000;
}

function setSessionFromLogin(response: LoginResponse): void {
  accessToken = response.access_token;
  session = {
    userId: response.id,
    role: roleFromToken(response.access_token),
    email: response.email,
    name: response.name,
  };
}

export function getAccessToken(): string | null {
  return accessToken;
}

export function getAuthSession(): AuthSession | null {
  return session;
}

async function login(email: string, password: string): Promise<boolean> {
  const apiBase =
    import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8080';

  const response = await fetch(`${apiBase}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) return false;

  setSessionFromLogin((await response.json()) as LoginResponse);
  return true;
}

/** Dev bootstrap: POST /auth/login with seeded credentials before API calls. */
export async function ensureAuthSession(): Promise<void> {
  if (!import.meta.env.DEV) return;

  const email = import.meta.env.VITE_DEV_AUTH_EMAIL ?? 'admin1@f4k.dev';
  const password = import.meta.env.VITE_DEV_AUTH_PASSWORD ?? 'test123';

  const sessionMatchesDevAccount =
    session?.email.toLowerCase() === email.toLowerCase();
  const tokenStillValid =
    accessToken !== null && !isTokenExpired(accessToken);

  // Re-login when the dev account changes or the cached token is stale.
  if (tokenStillValid && sessionMatchesDevAccount) return;

  const ok = await login(email, password);
  if (!ok) {
    console.warn(
      '[auth] POST /auth/login failed — run seed_database and check credentials.'
    );
  }
}
