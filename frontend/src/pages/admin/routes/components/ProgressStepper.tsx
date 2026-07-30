import { Fragment } from 'react';

import CheckIcon from '@/assets/icons/check.svg?react';
import { cn } from '@/lib/utils';

interface Step {
  label: string;
  path: string;
}

const STEPS: Step[] = [
  { label: 'Import', path: '/admin/routes/generation/import' },
  { label: 'Validate', path: '/admin/routes/generation/validate' },
  { label: 'Review Changes', path: '/admin/routes/generation/review' },
  { label: 'Edit Route Groups', path: '/admin/routes/generation/configure' },
  { label: 'Generate Routes', path: '/admin/routes/generation/generate' },
];

interface ProgressStepperProps {
  currentStep: number;
  className?: string;
}

function ProgressStepper({ currentStep, className }: ProgressStepperProps) {
  return (
    // Each step is as wide as its own label, with the connectors sharing what
    // is left over — so the labels sit centred on their circles and the track
    // stops where the last label ends. Absolutely positioning the labels over
    // fixed 24px columns instead spread the circles edge to edge, which pushed
    // every label right of where the frames put it (up to 86px by the middle).
    // 24px circle + 4px + 20px label is the frame's 48px stepper exactly, so
    // no bottom padding: the 40px to the next section is the parent's gap.
    <div className={cn('flex w-full items-start gap-8', className)}>
      {STEPS.map((step, i) => (
        <Fragment key={step.path}>
          <div className="relative z-10 flex shrink-0 flex-col items-center gap-1">
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
                'text-h3 text-center font-bold whitespace-nowrap',
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
