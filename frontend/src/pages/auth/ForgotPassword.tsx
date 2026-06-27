import { type FormEvent, useState } from 'react';

import { useForgotPassword } from '@/api';
import { Button, Field, FieldLabel, Input } from '@/common/components';
import { WrapperWithLogo } from './Wrapper';
import { Link } from 'react-router-dom';

type Step = 'FORM' | 'CONFIRMATION';

export const ForgotPassword = () => {
  const [step, setStep] = useState<Step>('FORM');
  const headerTitle = step === 'FORM' ? "Forgot password?" : "Reset link sent"
  const subheaderTitle = step === 'FORM' ? 'What email did your admin use to sign you up?' : 'If an account exists for that email, we’ve sent a link to reset your password. It may take a few minutes to arrive.';

  return (
    <WrapperWithLogo 
      headerTitle={headerTitle}
      subheaderTitle={subheaderTitle}
      className="desktop:max-w-[362px]"
    >
      {step === 'FORM' ? (
        <ForgotPasswordForm onSuccess={() => setStep('CONFIRMATION')} />
      ) : (
        <ResetLinkConfirmation />
      )}
    </WrapperWithLogo>
  );
}

interface ForgotPasswordFormProps {
  onSuccess: () => void;
}

const ForgotPasswordForm = ({ onSuccess }: ForgotPasswordFormProps) => {
  const [email, setEmail] = useState('');

  const forgotPasswordMutation = useForgotPassword();

  const handleForgotPassword = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    
    forgotPasswordMutation.mutate(
      { email },
      {
        onSuccess: () => {
          onSuccess();
        },
      }
    );
  };

  return (
    <>
      <div>
        {/* Form */}
        <form onSubmit={handleForgotPassword} className="flex flex-col gap-6">
          {/* Email Field */}
          <Field>
            <FieldLabel htmlFor="email">Email</FieldLabel>
            <Input
              id="email"
              className='px-6'
              type="email"
              autoComplete="email"
              placeholder="Enter your email"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
              }}
              required
            />
          </Field>

          {/* Send Link Button */}
          <Button
            type="submit"
            variant="primary"
            shape="default"
            className="mt-6 w-full py-3"
            disabled={forgotPasswordMutation.isPending}
          >
            Send link
          </Button>
        </form>

        {/* Footer */}
        <p className="desktop:mt-5 text-m-p2 tablet:font-medium tablet:mb-0 mt-6 mb-8 text-center">
          <Link
            to="/login"
            className="text-blue-300 hover:underline"
          >
            Return to login
          </Link>
        </p>
      </div>
    </>
  )
}

const ResetLinkConfirmation = () => {
  return <></>
}
