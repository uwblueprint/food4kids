import { ChevronLeftIcon } from 'lucide-react';
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { useUpdatePasswordAuthed } from '@/api/auth';
import { describeApiFailure } from '@/api/errors';
import { UpdatePasswordForm } from '@/pages/auth/UpdatePasswordForm';

export const UpdatePasswordPage = () => {
  const navigate = useNavigate();
  const [submitError, setSubmitError] = useState<string | null>(null);
  const { mutate, isPending } = useUpdatePasswordAuthed();

  const handleSubmit = (currentPassword: string, newPassword: string) => {
    setSubmitError(null);
    mutate(
      {
        current_password: currentPassword,
        new_password: newPassword,
      },
      {
        onSuccess: () => {
          navigate('/driver/profile');
        },
        onError: (error) => {
          const message = describeApiFailure(error);
          setSubmitError(
            message || 'Incorrect current password.'
          );
        },
      }
    );
  };

  return (
    <main className="flex flex-col items-center gap-6 mx-auto w-full">
      <Link
        to="/driver/home"
        className="flex gap-1 text-blue-400 self-start"
      >
        <ChevronLeftIcon className="size-6" />
        <h2>Back to home</h2>
      </Link>

      <div className="flex gap-1 w-full">
        <h1>
          Change password
        </h1>
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
