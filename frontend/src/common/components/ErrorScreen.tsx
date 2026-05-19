import { type ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';

import error403Img from '@/assets/errors/error-403.png';
import error404Img from '@/assets/errors/error-404.png';
import error503Img from '@/assets/errors/error-503.png';
import boyEdgeCaseImg from '@/assets/illustrations/boy-edge-case-with-questions.png';

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
      <div className="flex w-full flex-col items-center">
        <img
          src={illustration}
          alt=""
          aria-hidden
          className="mb-3 h-60 w-full object-contain"
        />
        <h2 className="text-grey-500 mb-5 text-center text-3xl leading-10 font-bold">
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
    <ErrorScreen illustration={error404Img} title="Page not found">
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
    <ErrorScreen illustration={error403Img} title="Forbidden">
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
    <ErrorScreen illustration={error503Img} title="Service Unavailable">
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
