import { Fragment } from 'react';

import CheckIcon from '@/assets/icons/check.svg?react';
import { cn } from '@/lib/utils';
import { useNavigate } from 'react-router-dom';

interface Step {
  label: string;
  path: string;
}

const STEPS: Step[] = [
  { label: 'Import', path: '/admin/routes/generation/import' },
  { label: 'Validate', path: '/admin/routes/generation/validate' },
  { label: 'Review Changes', path: '/admin/routes/generation/review' },
  { label: 'Configure Routes', path: '/admin/routes/generation/configure' },
  { label: 'Generate Routes', path: '/admin/routes/generation/generate' },
];

interface ProgressStepperProps {
  currentStep: number;
  className?: string;
}

function ProgressStepper({ currentStep, className }: ProgressStepperProps) {
  const navigate = useNavigate();

  return (
    <div className={cn('flex w-full items-start pb-6', className)}>
      {STEPS.map((step, i) => (
        <Fragment key={step.path}>
          <div className="relative z-10 m-0 flex w-6 shrink-0 justify-center">
            <div
              onClick={() => currentStep > i && navigate(step.path)}
              className={cn(
                'flex size-6 cursor-pointer items-center justify-center rounded-full border-2 bg-white',
                i < currentStep && 'border-blue-300 bg-blue-300',
                i === currentStep && 'border-blue-300 bg-white',
                i > currentStep && 'border-grey-300 bg-white'
              )}
            >
              {i < currentStep && <CheckIcon className="size-3.5 text-white" />}
            </div>
            <span
              className={cn(
                'text-h3 absolute top-8 left-1/2 -translate-x-1/2 text-center font-bold whitespace-nowrap',
                i <= currentStep ? 'text-blue-300' : 'text-grey-400'
              )}
            >
              {step.label}
            </span>
          </div>
          {i + 1 < STEPS.length && (
            <div
              className={cn(
                'mt-3 h-0.5 flex-1 -translate-y-1/2',
                i < currentStep ? 'bg-blue-300' : 'bg-grey-300'
              )}
            />
          )}
        </Fragment>
      ))}
    </div>
  );
}

export { ProgressStepper };
