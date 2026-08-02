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
    // The circles are evenly spaced and the labels hang off them: each label is
    // centred on its circle and taken out of the flow, so a label as wide as
    // "Edit Route Groups" doesn't push its circle around. That leaves the row as
    // fixed-size circles with the connectors splitting whatever is left over.
    // `pb-6` reserves the 4px gap + 20px line the labels occupy, and `px-14`
    // the half-label that the first and last circles' labels hang off the row —
    // without it they escape the page's side padding and cause a horizontal
    // scroll. 56px clears the widest end label ("Generate Routes", 50.5px of
    // overhang); bump it if the end labels get longer.
    <div className={cn('flex w-full items-center px-14 pb-6', className)}>
      {STEPS.map((step, i) => (
        <Fragment key={step.path}>
          {i > 0 && (
            <div
              className={cn(
                'h-[3px] flex-1',
                i <= currentStep ? 'bg-blue-300' : 'bg-grey-300'
              )}
            />
          )}
          <div
            className={cn(
              'relative flex size-6 shrink-0 items-center justify-center rounded-full border-2',
              i < currentStep && 'border-blue-300 bg-blue-300',
              i === currentStep && 'border-blue-300',
              i > currentStep && 'border-grey-400'
            )}
          >
            {i < currentStep && <CheckIcon className="size-3.5 text-white" />}
            <span
              className={cn(
                'text-h3 absolute top-full left-1/2 mt-1 -translate-x-1/2 font-bold whitespace-nowrap',
                i <= currentStep ? 'text-blue-300' : 'text-grey-400'
              )}
            >
              {step.label}
            </span>
          </div>
        </Fragment>
      ))}
    </div>
  );
}

export { ProgressStepper };
