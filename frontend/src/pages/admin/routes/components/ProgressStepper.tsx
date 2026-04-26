import { Fragment } from 'react';

import CheckIcon from '@/assets/icons/check.svg?react';
import { cn } from '@/lib/utils';

const STEPS = [
  'Import',
  'Validate',
  'Review Changes',
  'Configure Routes',
  'Generate Routes',
] as const;

interface ProgressStepperProps {
  currentStep: number;
  className?: string;
}

function ProgressStepper({ currentStep, className }: ProgressStepperProps) {
  return (
    <div className={cn('flex w-full items-start pb-6', className)}>
      {STEPS.map((label, i) => (
        <Fragment key={label}>
          <div className="relative z-10 m-0 flex w-6 shrink-0 justify-center">
            <div
              className={cn(
                'flex size-6 items-center justify-center rounded-full border-2 bg-white',
                i < currentStep && 'border-blue-300 bg-blue-300',
                i === currentStep && 'border-blue-300 bg-white',
                i > currentStep && 'border-grey-300 bg-white'
              )}
            >
              {i < currentStep && <CheckIcon className="size-3.5 text-white" />}
            </div>
            <span
              className={cn(
                'text-h3 absolute top-8 left-1/2 -translate-x-1/2 whitespace-nowrap text-center font-bold',
                i <= currentStep ? 'text-blue-300' : 'text-grey-400'
              )}
            >
              {label}
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
