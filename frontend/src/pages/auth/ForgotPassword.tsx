import { useState } from 'react';

import { useForgotPassword } from '@/api';

import { RequestLinkForm, SendLinkConfirmation } from './RequestLinkForm';
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

  const handleSendLink = (submittedEmail: string) => {
    forgotPasswordMutation.mutate(
      { email: submittedEmail },
      {
        onSuccess: () => {
          setStep('CONFIRMATION');
        },
      }
    );
  };

  const handleResendLink = (submittedEmail: string) => {
    forgotPasswordMutation.mutate({ email: submittedEmail });
  };

  return (
    <WrapperWithLogo
      headerTitle={headerTitle}
      subheaderTitle={subheaderTitle}
      className="desktop:max-w-[362px] desktop:gap-8 gap-4 pt-35"
    >
      {step === 'FORM' ? (
        <RequestLinkForm
          email={email}
          setEmail={setEmail}
          onSubmit={handleSendLink}
          isPending={forgotPasswordMutation.isPending}
        />
      ) : (
        <SendLinkConfirmation
          email={email}
          onResend={handleResendLink}
          isPending={forgotPasswordMutation.isPending}
        />
      )}
    </WrapperWithLogo>
  );
};
