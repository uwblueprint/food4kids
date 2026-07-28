import { useState } from 'react';

import { useForgotPassword } from '@/api';

import { RequestLinkForm, SendLinkConfirmation } from './RequestLinkForm';
import { WrapperWithLogo } from './Wrapper';

type Step = 'FORM' | 'CONFIRMATION';

export const GetLoginLink = () => {
  const [step, setStep] = useState<Step>('FORM');
  const [email, setEmail] = useState('');
  const headerTitle = step === 'FORM' ? 'Didn’t get a link?' : 'Login link sent';
  const subheaderTitle =
    step === 'FORM'
      ? "Enter the email address your admin used to invite you. We'll send a new login link."
      : "We've emailed your setup link. It may take a few minutes to land in your inbox.";

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
      className="desktop:max-w-[362px] desktop:gap-8 gap-4 pt-31"
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
