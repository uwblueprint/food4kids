export type AuthenticatedUser = {
  id: string;
  name: string;
  email: string;
  accessToken: string;
} | null;

export type AuthError = {
  code: string;
  message: string;
};

export type AuthState = {
  user: AuthenticatedUser;
  loading: boolean;
  error: AuthError | null;
};
