export const getFirebaseErrorMessage = (errorCode: string): string => {
  const errorMessages: Record<string, string> = {
    'auth/invalid-email': 'Invalid email address format.',
    'auth/user-disabled': 'This account has been disabled.',
    'auth/user-not-found': 'Invalid email or password.',
    'auth/wrong-password': 'Invalid email or password.',
    'auth/email-already-in-use': 'An account with this email already exists.',
    'auth/weak-password': 'Password should be at least 6 characters.',
    'auth/operation-not-allowed': 'This sign-in method is not enabled.',
    'auth/popup-closed-by-user': 'Sign-in popup was closed before completion.',
    'auth/cancelled-popup-request':
      'Only one popup request is allowed at a time.',
    'auth/too-many-requests':
      'Too many failed attempts. Please try again later.',
    'auth/network-request-failed':
      'Network error. Please check your connection.',
  };

  return (
    errorMessages[errorCode] ||
    'An unexpected error occurred. Please try again.'
  );
};
