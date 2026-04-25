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
    <div className={cn('relative flex w-full justify-between', className)}>
      {/* TODO: Single line behind all circles — left-3/right-3 trims to circle centers */}
      <div className="bg-grey-300 absolute top-3 right-6 left-6 h-px" />

      {STEPS.map((label, i) => (
        <div
          key={label}
          className="relative z-10 flex flex-col items-center gap-1"
        >
          <div
            className={cn(
              'flex size-6 items-center justify-center rounded-full border-2 bg-white',
              i < currentStep && 'border-blue-300 bg-blue-300',
              i === currentStep && 'border-blue-300 bg-white',
              i > currentStep && 'border-grey-300 bg-white'
            )}
          >
            {i < currentStep && (
              <CheckIcon className="size-3.5 text-white" />
            )}
          </div>
          <span
            className={cn(
              'text-h3 text-center font-bold whitespace-nowrap',
              i <= currentStep ? 'text-blue-300' : 'text-grey-400'
            )}
          >
            {label}
          </span>
        </div>
      ))}
    </div>
  );
}

export { ProgressStepper };
