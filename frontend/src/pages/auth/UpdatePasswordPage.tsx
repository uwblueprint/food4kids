import { ChevronLeftIcon } from 'lucide-react';
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { useUpdatePasswordAuthed } from '@/api/auth';
import { useAuthStore } from '@/api/authStore';
import { describeApiFailure } from '@/api/errors';
import { cn } from '@/lib/utils';
import { UpdatePasswordForm } from '@/pages/auth/UpdatePasswordForm';

export const UpdatePasswordPage = () => {
  const navigate = useNavigate();
  const isAdmin = useAuthStore((state) => state.user?.role === 'admin');
  const [submitError, setSubmitError] = useState<string | null>(null);
  const { mutate, isPending } = useUpdatePasswordAuthed();

  // Admins reach this from the account menu and have no profile page, so they
  // land back on their home instead.
  const homePath = isAdmin ? '/admin/home' : '/driver/home';
  const successPath = isAdmin ? '/admin/home' : '/driver/profile';

  const handleSubmit = (currentPassword: string, newPassword: string) => {
    setSubmitError(null);
    mutate(
      {
        current_password: currentPassword,
        new_password: newPassword,
      },
      {
        onSuccess: () => {
          navigate(successPath);
        },
        onError: (error) => {
          const message = describeApiFailure(error);
          setSubmitError(message || 'Incorrect current password.');
        },
      }
    );
  };

  return (
    <main
      className={cn(
        'mx-auto flex w-full flex-col items-center gap-6',
        isAdmin && 'max-w-[600px]'
      )}
    >
      <Link to={homePath} className="flex gap-1 self-start text-blue-400">
        <ChevronLeftIcon className="size-6" />
        <h2>Back to home</h2>
      </Link>

      <div className="flex w-full gap-1">
        <h1>Change password</h1>
      </div>

      <div className="w-full">
        <UpdatePasswordForm
          onSubmit={handleSubmit}
          isPending={isPending}
          submitButtonText="Update password"
          submitError={submitError}
        />
      </div>
    </main>
  );
};
