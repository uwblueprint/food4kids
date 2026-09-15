import { useState } from 'react';

import { describeApiFailure, useResendOnboardingEmail } from '@/api';

import { RequestLinkForm, SendLinkConfirmation } from './RequestLinkForm';
import { WrapperWithLogo } from './Wrapper';

const sendFailureMessage = (error: unknown) =>
  describeApiFailure(error) ??
  'We couldn’t send the login link. Please try again in a moment.';

type Step = 'FORM' | 'CONFIRMATION';

export const GetLoginLink = () => {
  const [step, setStep] = useState<Step>('FORM');
  const [email, setEmail] = useState('');
  const [hasResent, setHasResent] = useState(false);
  const [sendError, setSendError] = useState<string | null>(null);
  const [resendError, setResendError] = useState<string | null>(null);

  const getHeaderTitle = (currentStep: Step, linkResent: boolean) => {
    if (currentStep === 'FORM') {
      return 'Didn’t get a link?';
    }

    if (linkResent) {
      return 'Login link resent';
    }

    return 'Login link sent';
  };

  const headerTitle = getHeaderTitle(step, hasResent);

  const getSubheaderTitle = (currentStep: Step, linkResent: boolean) => {
    if (currentStep === 'FORM') {
      return "Enter the email address your admin used to invite you. We'll send a new login link.";
    }

    if (linkResent) {
      return "We've emailed you another login link. It may take a few minutes to land in your inbox.\n\nPlease check your spam/junk folders too. If you still don’t see anything after 10 minutes, please reach out to your admin for help.";
    }

    return "We've emailed your login link. It may take a few minutes to land in your inbox.";
  };

  const subheaderTitle = getSubheaderTitle(step, hasResent);

  const resendOnboardingEmailMutation = useResendOnboardingEmail();

  const handleSendLink = (submittedEmail: string) => {
    setSendError(null);
    resendOnboardingEmailMutation.mutate(
      { email: submittedEmail },
      {
        onSuccess: () => {
          setStep('CONFIRMATION');
        },
        onError: (error) => {
          setSendError(sendFailureMessage(error));
        },
      }
    );
  };

  const handleResendLink = (
    submittedEmail: string,
    options?: { onError?: (error: unknown) => void }
  ) => {
    setResendError(null);
    resendOnboardingEmailMutation.mutate(
      { email: submittedEmail },
      {
        onSuccess: () => {
          setHasResent(true);
        },
        onError: (error) => {
          setResendError(sendFailureMessage(error));
          options?.onError?.(error);
        },
      }
    );
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
          isPending={resendOnboardingEmailMutation.isPending}
          sendError={sendError}
          clearError={() => setSendError(null)}
        />
      ) : (
        <SendLinkConfirmation
          email={email}
          onResend={handleResendLink}
          isPending={resendOnboardingEmailMutation.isPending}
          resendError={resendError}
          clearError={() => setResendError(null)}
        />
      )}
    </WrapperWithLogo>
  );
};
