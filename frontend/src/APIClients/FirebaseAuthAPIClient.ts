import { auth } from '../config/firebase';
import baseAPIClient from './BaseAPIClient';
import { AuthenticatedUser } from '../types/AuthTypes';

/**
 * Syncs Firebase user with backend and returns user data
 */
const syncUserWithBackend = async (
  idToken: string,
): Promise<AuthenticatedUser> => {
  try {
    const { data } = await baseAPIClient.post(
      '/auth/oauth',
      { id_token: idToken },
      { withCredentials: true },
    );
    return data;
  } catch (error) {
    console.error('Failed to sync user with backend:', error);
    throw error;
  }
};

/**
 * Gets current Firebase ID token for API requests
 */
const getIdToken = async (): Promise<string | null> => {
  const user = auth.currentUser;
  if (!user) return null;

  try {
    return await user.getIdToken();
  } catch (error) {
    console.error('Failed to get ID token:', error);
    return null;
  }
};

/**
 * Logout user (revoke tokens on backend)
 */
const logout = async (userId: string): Promise<boolean> => {
  const idToken = await getIdToken();
  if (!idToken) return false;

  try {
    await baseAPIClient.post(
      `/auth/logout/${userId}`,
      {},
      { headers: { Authorization: `Bearer ${idToken}` } },
    );
    return true;
  } catch (error) {
    console.error('Logout failed:', error);
    return false;
  }
};

/**
 * Request password reset email
 */
const resetPassword = async (email: string): Promise<boolean> => {
  const idToken = await getIdToken();
  if (!idToken) return false;

  try {
    await baseAPIClient.post(
      `/auth/resetPassword/${email}`,
      {},
      { headers: { Authorization: `Bearer ${idToken}` } },
    );
    return true;
  } catch (error) {
    console.error('Password reset failed:', error);
    return false;
  }
};

export default {
  syncUserWithBackend,
  getIdToken,
  logout,
  resetPassword,
};
