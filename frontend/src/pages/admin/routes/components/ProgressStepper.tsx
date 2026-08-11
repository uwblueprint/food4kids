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

/**
 * The 3px rule. Inside a step it sits in a centre-aligned row, so it lines up
 * with the circle on its own; the connectors between steps hang off the top of
 * the row instead and need CONNECTOR_DROP to meet them.
 */
const CONNECTOR = 'h-[3px]';
/** (24px circle − 3px rule) / 2, so the two meet without a step in the line. */
const CONNECTOR_DROP = 'mt-[10.5px]';

interface ProgressStepperProps {
  currentStep: number;
  className?: string;
}

function ProgressStepper({ currentStep, className }: ProgressStepperProps) {
  return (
    // The frames lay this out as five label-sized boxes with equal gaps, each
    // circle centred over its own label — not as evenly spaced circles with
    // labels hanging off them. The difference is visible: even spacing puts
    // "Review Changes" 52px right of where the frame has it. So each step is an
    // in-flow column (circle over label) and the connectors take the slack,
    // which also means the end labels sit flush with the row's edges on their
    // own — no measuring, no end inset.
    <div className={cn('flex w-full items-start', className)}>
      {STEPS.map((step, i) => {
        // The line reaching step i is blue once that step has been passed; the
        // one leaving it, once the next has.
        const lineIn = i <= currentStep ? 'bg-blue-300' : 'bg-grey-300';
        const lineOut = i + 1 <= currentStep ? 'bg-blue-300' : 'bg-grey-300';
        return (
          <Fragment key={step.path}>
            {i > 0 && (
              <div
                className={cn(CONNECTOR, CONNECTOR_DROP, 'flex-1', lineIn)}
              />
            )}
            <div className="flex shrink-0 flex-col items-center gap-1">
              {/* The column is as wide as its label, so the circle alone would
                  leave a gap either side of it. These two segments fill that
                  gap, joining the circle to the connectors between columns —
                  blank on the outer side of the first and last steps, which
                  have no line to reach. */}
              <div className="flex w-full items-center">
                <div
                  className={cn(CONNECTOR, 'flex-1', i > 0 && lineIn)}
                  aria-hidden
                />
                <div
                  className={cn(
                    'flex size-6 shrink-0 items-center justify-center rounded-full border-2',
                    i < currentStep && 'border-blue-300 bg-blue-300',
                    i === currentStep && 'border-blue-300',
                    i > currentStep && 'border-grey-400'
                  )}
                >
                  {i < currentStep && (
                    <CheckIcon className="size-3.5 text-white" />
                  )}
                </div>
                <div
                  className={cn(
                    CONNECTOR,
                    'flex-1',
                    i < STEPS.length - 1 && lineOut
                  )}
                  aria-hidden
                />
              </div>
              <span
                className={cn(
                  'text-h3 font-bold whitespace-nowrap',
                  i <= currentStep ? 'text-blue-300' : 'text-grey-400'
                )}
              >
                {step.label}
              </span>
            </div>
          </Fragment>
        );
      })}
    </div>
  );
}

export { ProgressStepper };
