import { useState } from 'react';
import { Navigate, useNavigate, useParams } from 'react-router-dom';

import { useRegisterDriver } from '@/api/auth';
import { Button } from '@/common/components';

import { CreatePasswordForm } from './CreatePasswordForm';
import { WrapperWithLogo } from './Wrapper';

type Step = 'FORM' | 'CONFIRMATION';

export const CreatePassword = () => {
  const [step, setStep] = useState<Step>('FORM');
  const headerTitle = step === 'FORM' ? 'Create a password' : 'Account created';
  const subheaderTitle =
    step === 'FORM'
      ? 'Create an account to access the app'
      : "You're in! Get ready to help fill some lunch bags and put smiles on some faces.";

  const { mutate, isPending } = useRegisterDriver();

  const { token } = useParams();
  const uuidRegex =
    /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  const isValidUuid = token && uuidRegex.test(token);

  if (!isValidUuid) {
    return <Navigate to="/404" replace />;
  }

  const handleRegister = (password: string) => {
    if (!token) return;

    mutate(
      {
        user_invite_id: token,
        password: password,
      },
      {
        onSuccess: () => setStep('CONFIRMATION'),
      }
    );
  };

  return (
    <WrapperWithLogo
      headerTitle={headerTitle}
      subheaderTitle={subheaderTitle}
      className="desktop:max-w-[362px]"
    >
      {step === 'FORM' ? (
        <CreatePasswordForm
          onSubmit={handleRegister}
          isPending={isPending}
          submitButtonText="Create account"
        />
      ) : (
        <AccountCreationConfirmation />
      )}
    </WrapperWithLogo>
  );
};

const AccountCreationConfirmation = () => {
  const navigate = useNavigate();

  return (
    <>
      <div className="flex flex-col">
        <Button
          type="button"
          variant="primary"
          shape="default"
          className="desktop:mt-4 w-full py-3"
          onClick={() => navigate('/')}
        >
          Continue
        </Button>
      </div>
    </>
  );
};
