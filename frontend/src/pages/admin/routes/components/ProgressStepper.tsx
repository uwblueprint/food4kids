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

/** A 3px segment of the track, sitting on the 24px circle's centre line. */
function Track({ done, className }: { done: boolean; className?: string }) {
  return (
    <div
      className={cn(
        'absolute top-[10.5px] h-[3px]',
        done ? 'bg-blue-300' : 'bg-grey-300',
        className
      )}
    />
  );
}

function ProgressStepper({ currentStep, className }: ProgressStepperProps) {
  const last = STEPS.length - 1;

  return (
    // Each step is as wide as its own label, and the spans between them share
    // what is left over — which is what the frames do: the five labels sit at
    // an even 180.25px pitch across the content column, with each circle
    // centred on its own label.
    //
    // That leaves the circles unevenly spaced, so a span can't be one element:
    // it runs from a circle's edge, across the rest of that label's box, over
    // the gap, and into the next label's box. Hence three pieces — two drawn
    // inside the step columns and one filling the gap — which join up into an
    // unbroken line without anyone having to measure a label.
    <div className={cn('flex w-full items-start', className)}>
      {STEPS.map((step, i) => (
        <Fragment key={step.path}>
          <div className="relative flex shrink-0 flex-col items-center gap-1">
            {i > 0 && (
              <Track
                done={i - 1 < currentStep}
                className="right-[calc(50%+12px)] left-0"
              />
            )}
            {i < last && (
              <Track
                done={i < currentStep}
                className="right-0 left-[calc(50%+12px)]"
              />
            )}
            <div
              className={cn(
                'relative flex size-6 items-center justify-center rounded-full border-2',
                i < currentStep && 'border-blue-300 bg-blue-300',
                i === currentStep && 'border-blue-300',
                i > currentStep && 'border-grey-400'
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
          {i < last && (
            <div className="relative flex-1">
              <Track done={i < currentStep} className="inset-x-0" />
            </div>
          )}
        </Fragment>
      ))}
    </div>
  );
}

export { ProgressStepper };
