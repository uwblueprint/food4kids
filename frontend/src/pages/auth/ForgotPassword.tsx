import { type FormEvent, useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { describeApiFailure, useForgotPassword } from '@/api';
import { Button, Field, FieldLabel, Input } from '@/common/components';

import { ErrorNote } from './ErrorNote';
import { WrapperWithLogo } from './Wrapper';

/**
 * The endpoint answers 204 whether or not the address exists, which is the
 * anti-enumeration design. A failure here is therefore never about the email the
 * user typed, and is never worth implying it was.
 */
const sendFailureMessage = (error: unknown) =>
  describeApiFailure(error) ??
  'We couldn’t send the reset link. Please try again in a moment.';

type Step = 'FORM' | 'CONFIRMATION';

export const ForgotPassword = () => {
  const [step, setStep] = useState<Step>('FORM');
  const [email, setEmail] = useState('');
  const headerTitle = step === 'FORM' ? 'Forgot password?' : 'Reset link sent';
  const subheaderTitle =
    step === 'FORM'
      ? 'What email did your admin use to sign you up?'
      : 'If an account exists for that email, we’ve sent a link to reset your password. It may take a few minutes to arrive.';

  const forgotPasswordMutation = useForgotPassword();

  return (
    <WrapperWithLogo
      headerTitle={headerTitle}
      subheaderTitle={subheaderTitle}
      className="desktop:max-w-[362px] desktop:gap-8 gap-4 pt-35"
    >
      {step === 'FORM' ? (
        <ForgotPasswordForm
          email={email}
          setEmail={setEmail}
          mutation={forgotPasswordMutation}
          onSuccess={() => setStep('CONFIRMATION')}
        />
      ) : (
        <ResetLinkConfirmation
          email={email}
          mutation={forgotPasswordMutation}
        />
      )}
    </WrapperWithLogo>
  );
};

interface ForgotPasswordFormProps {
  email: string;
  setEmail: (email: string) => void;
  mutation: ReturnType<typeof useForgotPassword>;
  onSuccess: () => void;
}

const ForgotPasswordForm = ({
  email,
  setEmail,
  mutation,
  onSuccess,
}: ForgotPasswordFormProps) => {
  const [sendError, setSendError] = useState<string | null>(null);

  const handleForgotPassword = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    setSendError(null);
    mutation.mutate(
      { email },
      {
        onSuccess: () => {
          onSuccess();
        },
        onError: (error) => {
          setSendError(sendFailureMessage(error));
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
              className="px-6"
              type="email"
              autoComplete="email"
              placeholder="Enter your email"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                setSendError(null);
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
            disabled={mutation.isPending}
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
    </>
  );
};

interface ResetLinkConfirmationProps {
  email: string;
  mutation: ReturnType<typeof useForgotPassword>;
}

const ResetLinkConfirmation = ({
  email,
  mutation,
}: ResetLinkConfirmationProps) => {
  const navigate = useNavigate();
  const [countdown, setCountdown] = useState(60);
  const [resendError, setResendError] = useState<string | null>(null);

  useEffect(() => {
    if (countdown === 0) return;

    const timer = setInterval(() => {
      setCountdown((prev) => prev - 1);
    }, 1000);

    return () => clearInterval(timer);
  }, [countdown]);

  const handleResendClick = () => {
    setResendError(null);
    mutation.mutate(
      { email },
      {
        onError: (error) => {
          // Nothing was sent, so don't make them wait out a countdown for it.
          setResendError(sendFailureMessage(error));
          setCountdown(0);
        },
      }
    );
    setCountdown(60);
  };

  return (
    <>
      {/* Send Link Button */}
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
            onClick={
              countdown > 0 || mutation.isPending
                ? undefined
                : handleResendClick
            }
            className={
              countdown > 0 || mutation.isPending
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
    </>
  );
};
