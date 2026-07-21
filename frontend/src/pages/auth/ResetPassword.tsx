import { Navigate, useNavigate, useParams } from 'react-router-dom';

import { useUpdatePassword, useValidateResetToken } from '@/api/auth';

import { CreatePasswordForm } from './CreatePasswordForm';
import { WrapperWithLogo } from './Wrapper';

export const ResetPassword = () => {
  const { token } = useParams();

  if (!token) {
    return <Navigate to="/404" replace />;
  }

  return <ResetPasswordContent token={token} />;
};

interface ResetPasswordContentProps {
  token: string;
}

const ResetPasswordContent = ({ token }: ResetPasswordContentProps) => {
  const headerTitle = 'Rest your password';
  const subheaderTitle = 'Create a password to access the app';

  const navigate = useNavigate();

  const { isLoading: isValidatingToken, isError: isTokenInvalid } =
    useValidateResetToken({ password_reset_token: token });

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

  if (isTokenInvalid) {
    return <Navigate to="/404" replace />;
  }

  const handleResetPassword = (password: string) => {
    mutate(
      {
        password_reset_token: token,
        new_password: password,
      },
      {
        onSuccess: () => {
          navigate('/login', { replace: true });
        },
        onError: () => {
          navigate('/error', { replace: true });
        },
      }
    );
  };

  return (
    <WrapperWithLogo
      headerTitle={headerTitle}
      subheaderTitle={subheaderTitle}
      className="desktop:max-w-[362px]"
    >
      <CreatePasswordForm
        onSubmit={handleResetPassword}
        isPending={isPending}
        submitButtonText="Create account"
      />
    </WrapperWithLogo>
  );
};
