import { type FormEvent, useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { Button, Field, FieldLabel, Input } from '@/common/components';

import { ErrorNote } from './ErrorNote';

interface RequestLinkFormProps {
  email: string;
  setEmail: (email: string) => void;
  onSubmit: (email: string) => void;
  isPending: boolean;
  sendError: string | null;
  clearError: () => void;
}

export const RequestLinkForm = ({
  email,
  setEmail,
  onSubmit,
  isPending,
  sendError,
  clearError,
}: RequestLinkFormProps) => {
  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    onSubmit(email);
  };

  return (
    <div>
      {/* Form */}
      <form onSubmit={handleSubmit} className="flex flex-col gap-6">
        {/* Email Field */}
        <Field>
          <FieldLabel htmlFor="email">Email</FieldLabel>
          <Input
            id="email"
            className="px-6"
            type="email"
            autoComplete="email"
            placeholder="Enter your email"
            value={email}
            onChange={(e) => {
              setEmail(e.target.value);
              clearError();
            }}
            required
          />
        </Field>

        {sendError && <ErrorNote className="-mb-2">{sendError}</ErrorNote>}

        {/* Send Link Button */}
        <Button
          type="submit"
          variant="primary"
          shape="default"
          className="desktop:mt-6 mt-2 w-full py-3"
          disabled={isPending}
        >
          Send link
        </Button>
      </form>

      {/* Footer */}
      <p className="desktop:mt-5 text-m-p2 tablet:font-medium tablet:mb-0 mt-6 mb-8 text-center">
        <Link to="/login" className="text-blue-300 hover:underline">
          Return to login
        </Link>
      </p>
    </div>
  );
};

interface SendLinkConfirmationProps {
  email: string;
  onResend: (
    email: string,
    options?: { onError?: (error: unknown) => void }
  ) => void;
  isPending: boolean;
  resendError: string | null;
  clearError: () => void;
}

export const SendLinkConfirmation = ({
  email,
  onResend,
  isPending,
  resendError,
  clearError,
}: SendLinkConfirmationProps) => {
  const navigate = useNavigate();
  const [countdown, setCountdown] = useState(60);

  useEffect(() => {
    if (countdown === 0) {
      return;
    }

    const timer = setInterval(() => {
      setCountdown((prev) => prev - 1);
    }, 1000);

    return () => clearInterval(timer);
  }, [countdown]);

  const handleResendClick = () => {
    clearError();
    onResend(email, {
      onError: () => {
        setCountdown(0);
      },
    });
    setCountdown(60);
  };

  return (
    <div className="flex flex-col">
      <Button
        type="button"
        variant="primary"
        shape="default"
        className="desktop:mt-2 w-full py-3"
        onClick={() => navigate('/login')}
      >
        Return to login
      </Button>
      <p className="desktop:mt-2 text-m-p2 tablet:font-medium mt-3 py-3 text-center">
        <button
          type="button"
          onClick={countdown > 0 || isPending ? undefined : handleResendClick}
          className={
            countdown > 0 || isPending
              ? 'cursor-not-allowed text-gray-400'
              : 'cursor-pointer text-blue-300 hover:underline'
          }
        >
          {countdown > 0
            ? `Send again in ${countdown} seconds`
            : 'Send link again'}
        </button>
      </p>
      {resendError && (
        <ErrorNote className="justify-center text-center">
          {resendError}
        </ErrorNote>
      )}
    </div>
  );
};
