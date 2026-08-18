import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { useUpdatePassword, useValidateResetToken } from '@/api/auth';
import { describeApiFailure } from '@/api/errors';
import {
  CatchAllErrorPage,
  NotFoundPage,
  ServiceUnavailablePage,
} from '@/common/components';

import { CreatePasswordForm } from './CreatePasswordForm';
import { WrapperWithLogo } from './Wrapper';

export const ResetPassword = () => {
  const { token } = useParams();

  if (!token) {
    return <NotFoundPage />;
  }

  return <ResetPasswordContent token={token} />;
};

interface ResetPasswordContentProps {
  token: string;
}

const ResetPasswordContent = ({ token }: ResetPasswordContentProps) => {
  const headerTitle = 'Reset your password';
  const subheaderTitle = 'Create a password to access the app';

  const navigate = useNavigate();
  // A message means the reset never reached the server, so the form (and the
  // password already typed into it) stays put and the user can retry. Only a
  // refusal from the server itself is worth throwing the whole screen away.
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [hasSubmitError, setHasSubmitError] = useState(false);

  const {
    isLoading: isValidatingToken,
    isError: didValidationFail,
    error: validationError,
  } = useValidateResetToken({ password_reset_token: token });

  const { mutate, isPending } = useUpdatePassword();

  if (isValidatingToken) {
    return (
      <WrapperWithLogo
        headerTitle={headerTitle}
        subheaderTitle="Verifying link safety..."
        className="desktop:max-w-[362px]"
      >
        <div className="flex justify-center p-8 text-neutral-500">
          Checking token validity...
        </div>
      </WrapperWithLogo>
    );
  }

  if (didValidationFail) {
    // A link we couldn't check is not a link we can call dead. The backend
    // answers 400 for a token that's really expired, and nothing at all when
    // it's the connection that's gone.
    return describeApiFailure(validationError) ? (
      <ServiceUnavailablePage />
    ) : (
      <NotFoundPage />
    );
  }

  if (hasSubmitError) {
    return <CatchAllErrorPage />;
  }

  const handleResetPassword = (password: string) => {
    setConnectionError(null);
    mutate(
      {
        password_reset_token: token,
        new_password: password,
      },
      {
        onSuccess: () => {
          navigate('/login', { replace: true });
        },
        onError: (error) => {
          const message = describeApiFailure(error);
          if (message) {
            setConnectionError(message);
          } else {
            setHasSubmitError(true);
          }
        },
      }
    );
  };

  return (
    <WrapperWithLogo
      headerTitle={headerTitle}
      subheaderTitle={subheaderTitle}
      className="desktop:max-w-[362px]"
      showMobileIllustration={false}
    >
      <CreatePasswordForm
        onSubmit={handleResetPassword}
        isPending={isPending}
        submitButtonText="Create account"
        submitError={connectionError}
      />
    </WrapperWithLogo>
  );
};
