import React from 'react';
import { Navigate } from 'react-router-dom';
import { useRefresh } from '@/api/auth';

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const { isPending, isError } = useRefresh();

  if (isPending) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-gray-50">
        <div className="flex flex-col items-center gap-2">
          <span className="text-sm font-medium text-gray-500">
            Restoring your session...
          </span>
        </div>
      </div>
    );
  }

  if (isError) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}
