import { type FormEvent, useState, useEffect } from 'react';

import { useForgotPassword } from '@/api';
import { Button, Field, FieldLabel, Input } from '@/common/components';
import { WrapperWithLogo } from './Wrapper';
import { Link } from 'react-router-dom';
import { useNavigate } from 'react-router-dom';

type Step = 'FORM' | 'CONFIRMATION';

export const ForgotPassword = () => {
  const [step, setStep] = useState<Step>('FORM');
  const [email, setEmail] = useState('');
  const headerTitle = step === 'FORM' ? "Forgot password?" : "Reset link sent"
  const subheaderTitle = step === 'FORM' ? 'What email did your admin use to sign you up?' : 'If an account exists for that email, we’ve sent a link to reset your password. It may take a few minutes to arrive.';

  const forgotPasswordMutation = useForgotPassword();

  return (
    <WrapperWithLogo 
      headerTitle={headerTitle}
      subheaderTitle={subheaderTitle}
      className="desktop:max-w-[362px] gap-4 desktop:gap-8 pt-31"
    >
      {step === 'FORM' ? (
        <ForgotPasswordForm 
          email={email}
          setEmail={setEmail}
          mutation={forgotPasswordMutation}
          onSuccess={() => setStep('CONFIRMATION')} />
      ) : (
        <ResetLinkConfirmation
        email={email}
        mutation={forgotPasswordMutation} />
      )}
    </WrapperWithLogo>
  );
}

interface ForgotPasswordFormProps {
  email: string;
  setEmail: (email: string) => void;
  mutation: ReturnType<typeof useForgotPassword>;
  onSuccess: () => void;
}

const ForgotPasswordForm = ({ email, setEmail, mutation, onSuccess }: ForgotPasswordFormProps) => {
  const handleForgotPassword = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    
    mutation.mutate(
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
            className="mt-2 desktop:mt-6 w-full py-3"
            disabled={mutation.isPending}
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

interface ResetLinkConfirmationProps {
  email: string;
  mutation: ReturnType<typeof useForgotPassword>;
}

const ResetLinkConfirmation = ({ email, mutation }: ResetLinkConfirmationProps) => {
  const navigate = useNavigate();
  const [countdown, setCountdown] = useState(60);

  useEffect(() => {
    if (countdown === 0) return;

    const timer = setInterval(() => {
      setCountdown((prev) => prev - 1);
    }, 1000);

    return () => clearInterval(timer);
  }, [countdown]);

  const handleResendClick = () => {
    mutation.mutate({ email });
    setCountdown(60); 
  };

  return <>
    {/* Send Link Button */}
    <div className="flex flex-col">
      <Button
        type="button"
        variant="primary"
        shape="default"
        className="desktop:mt-2 w-full py-3"
        onClick={() => navigate('/login')}
      >
        Back to log in
      </Button>
      <p className="mt-3 desktop:mt-2 py-3 text-center text-m-p2 tablet:font-medium">
        <span
          onClick={countdown > 0 || mutation.isPending ? undefined : handleResendClick}
          className={
            countdown > 0 || mutation.isPending
              ? "text-gray-400 cursor-not-allowed"
              : "text-blue-300 hover:underline cursor-pointer"
          }
        >
          {countdown > 0 ? `Send again in ${countdown} seconds` : 'Send link again'}
        </span>
      </p>
    </div>
  </>
}
