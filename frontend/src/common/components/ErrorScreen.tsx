import { type ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';

import boyEdgeCaseImg from '@/assets/illustrations/boy-edge-case-with-questions.png';
import girlForbiddenImg from '@/assets/illustrations/girl-403.png';
import girlCatchingImg from '@/assets/illustrations/girl-catching.png';
import grannyImg from '@/assets/illustrations/granny.png';
import { Button } from './Button';

interface ErrorScreenProps {
  illustration: string;
  title: string;
  children: ReactNode;
}

export function ErrorScreen({
  illustration,
  title,
  children,
}: ErrorScreenProps) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-white px-6">
      <div className="flex w-full max-w-[744px] flex-col items-center">
        <img
          src={illustration}
          alt=""
          aria-hidden
          className="h-80 w-56 object-contain"
        />
        <h2 className="font-nunito text-grey-500 mb-5 text-center text-3xl leading-10 font-bold">
          {title}
        </h2>
        {children}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Error Pages
// ---------------------------------------------------------------------------

export function NotFoundPage() {
  const navigate = useNavigate();
  return (
    <ErrorScreen illustration={grannyImg} title="404 - Page not found">
      <p className="text-grey-500 mb-12 text-center text-base leading-6">
        The page you're looking for doesn't exist or may have been moved.
      </p>
      <Button variant="primary" onClick={() => navigate(-1)}>
        Back
      </Button>
    </ErrorScreen>
  );
}

export function ForbiddenPage() {
  const navigate = useNavigate();
  return (
    <ErrorScreen illustration={girlForbiddenImg} title="403 - Forbidden">
      <p className="text-grey-500 mb-12 text-center text-base leading-6">
        This page is only available to authorized users. Please log in to
        continue.
      </p>
      {/* TODO: replace '/' with login route */}
      <Button variant="primary" onClick={() => navigate('/')}>
        Log In
      </Button>
    </ErrorScreen>
  );
}

export function ServiceUnavailablePage() {
  const navigate = useNavigate();
  return (
    <ErrorScreen illustration={girlCatchingImg} title="Service Unavailable">
      <div className="mb-12 flex flex-col items-center gap-1">
        <p className="text-grey-500 text-center text-base leading-6">
          We're temporarily offline for maintenance or unexpected issues.
        </p>
        <p className="text-grey-500 text-center text-base leading-6">
          Please try again shortly or return to the previous screen.
        </p>
      </div>
      <div className="flex gap-4">
        <Button variant="secondary" onClick={() => navigate(-1)}>
          Back
        </Button>
        <Button variant="primary" onClick={() => navigate(0)}>
          Refresh
        </Button>
      </div>
    </ErrorScreen>
  );
}

export function CatchAllErrorPage() {
  const navigate = useNavigate();
  return (
    <ErrorScreen illustration={boyEdgeCaseImg} title="Something went wrong">
      <p className="text-grey-500 mb-12 text-center text-base leading-6">
        Please try again shortly. If the issue persists, contact Emily Loro at
        (123) 456-7890 for help.
      </p>
      <Button variant="primary" onClick={() => navigate(-1)}>
        Back
      </Button>
    </ErrorScreen>
  );
}
