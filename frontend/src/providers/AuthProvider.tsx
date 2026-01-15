import React, { useState, useEffect, ReactNode } from 'react';
import {
  signInWithPopup,
  signInWithEmailAndPassword,
  signOut as firebaseSignOut,
  sendPasswordResetEmail,
  onAuthStateChanged,
  User as FirebaseUser,
} from 'firebase/auth';
import { auth, googleProvider } from '../config/firebase';
import AuthContext from '../contexts/AuthContext';
import { AuthenticatedUser } from '../types/AuthTypes';
import firebaseAuthAPIClient from '../APIClients/FirebaseAuthAPIClient';
import baseAPIClient from '../APIClients/BaseAPIClient';
import { getFirebaseErrorMessage } from '../utils/FirebaseErrors';
import AUTHENTICATED_USER_KEY from '../constants/AuthConstants';

type AuthProviderProps = {
  children: ReactNode;
};

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<AuthenticatedUser>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  // Listen to Firebase auth state changes
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(
      auth,
      async (firebaseUser: FirebaseUser | null) => {
        if (firebaseUser) {
          try {
            // Get Firebase ID token
            const idToken = await firebaseUser.getIdToken();

            // Sync with backend to get user data
            const userData =
              await firebaseAuthAPIClient.syncUserWithBackend(idToken);

            // Store user data
            localStorage.setItem(
              AUTHENTICATED_USER_KEY,
              JSON.stringify(userData),
            );
            setUser(userData);
          } catch (err) {
            console.error('Failed to sync user with backend:', err);
            setUser(null);
            localStorage.removeItem(AUTHENTICATED_USER_KEY);
          }
        } else {
          setUser(null);
          localStorage.removeItem(AUTHENTICATED_USER_KEY);
        }
        setLoading(false);
      },
    );

    return () => unsubscribe();
  }, []);

  const signInWithGoogle = async () => {
    setError(null);
    try {
      const result = await signInWithPopup(auth, googleProvider);
      const idToken = await result.user.getIdToken();

      // Sync with backend
      const userData =
        await firebaseAuthAPIClient.syncUserWithBackend(idToken);
      localStorage.setItem(AUTHENTICATED_USER_KEY, JSON.stringify(userData));
      setUser(userData);
    } catch (err: any) {
      const errorMessage = getFirebaseErrorMessage(err.code);
      setError(new Error(errorMessage));
      throw err;
    }
  };

  const signInWithEmail = async (email: string, password: string) => {
    setError(null);
    try {
      const result = await signInWithEmailAndPassword(auth, email, password);
      const idToken = await result.user.getIdToken();

      // Sync with backend
      const userData =
        await firebaseAuthAPIClient.syncUserWithBackend(idToken);
      localStorage.setItem(AUTHENTICATED_USER_KEY, JSON.stringify(userData));
      setUser(userData);
    } catch (err: any) {
      const errorMessage = getFirebaseErrorMessage(err.code);
      setError(new Error(errorMessage));
      throw err;
    }
  };

  const signUpWithEmail = async (
    email: string,
    password: string,
    name: string,
    phone: string,
    address: string,
    licensePlate: string,
    carMakeModel: string,
  ) => {
    setError(null);
    try {
      // First, register with backend (creates driver + Firebase user)
      await baseAPIClient.post('/auth/register', {
        email,
        password,
        name,
        phone,
        address,
        license_plate: licensePlate,
        car_make_model: carMakeModel,
      });

      // Then sign in with Firebase to get tokens
      const result = await signInWithEmailAndPassword(auth, email, password);
      const idToken = await result.user.getIdToken();

      // Sync with backend
      const userData =
        await firebaseAuthAPIClient.syncUserWithBackend(idToken);
      localStorage.setItem(AUTHENTICATED_USER_KEY, JSON.stringify(userData));
      setUser(userData);
    } catch (err: any) {
      const errorMessage = getFirebaseErrorMessage(err.code);
      setError(new Error(errorMessage));
      throw err;
    }
  };

  const signOut = async () => {
    setError(null);
    try {
      if (user) {
        await firebaseAuthAPIClient.logout(user.id);
      }
      await firebaseSignOut(auth);
      setUser(null);
      localStorage.removeItem(AUTHENTICATED_USER_KEY);
    } catch (err: any) {
      const errorMessage = getFirebaseErrorMessage(err.code);
      setError(new Error(errorMessage));
      throw err;
    }
  };

  const resetPassword = async (email: string) => {
    setError(null);
    try {
      await sendPasswordResetEmail(auth, email);
      await firebaseAuthAPIClient.resetPassword(email);
    } catch (err: any) {
      const errorMessage = getFirebaseErrorMessage(err.code);
      setError(new Error(errorMessage));
      throw err;
    }
  };

  const value = {
    user,
    loading,
    error,
    signInWithGoogle,
    signInWithEmail,
    signUpWithEmail,
    signOut,
    resetPassword,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
