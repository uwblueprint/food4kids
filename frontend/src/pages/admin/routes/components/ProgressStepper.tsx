import { Fragment, useLayoutEffect, useRef, useState } from 'react';

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

const CIRCLE_SIZE = 24;

interface ProgressStepperProps {
  currentStep: number;
  className?: string;
}

/**
 * How far the first and last labels stick out past their own circle. The track
 * is inset by exactly that much, so evenly-spaced circles can still carry
 * centred labels without the two end ones spilling over the page margins.
 * Measured rather than hardcoded because it depends on the rendered text —
 * a ResizeObserver so a late-loading webfont re-runs it.
 */
function useEndLabelOverhang() {
  const first = useRef<HTMLSpanElement>(null);
  const last = useRef<HTMLSpanElement>(null);
  const [overhang, setOverhang] = useState<[number, number]>([0, 0]);

  useLayoutEffect(() => {
    const measure = () => {
      if (!first.current || !last.current) return;
      setOverhang([
        Math.max(0, (first.current.offsetWidth - CIRCLE_SIZE) / 2),
        Math.max(0, (last.current.offsetWidth - CIRCLE_SIZE) / 2),
      ]);
    };
    measure();
    const observer = new ResizeObserver(measure);
    if (first.current) observer.observe(first.current);
    if (last.current) observer.observe(last.current);
    return () => observer.disconnect();
  }, []);

  return { first, last, overhang };
}

function ProgressStepper({ currentStep, className }: ProgressStepperProps) {
  const { first, last, overhang } = useEndLabelOverhang();

  return (
    // Circles are spaced evenly along the track with the connectors running
    // circle-edge to circle-edge between them, so the line is unbroken. Labels
    // are absolutely positioned and centred on their circle — in the flow they
    // would widen a step and push the circles around.
    // 24px circle + 4px + 20px label is the frame's 48px stepper, so the 24px
    // of bottom padding is what reserves room for the absolute labels.
    <div
      className={cn('flex w-full items-start pb-6', className)}
      style={{ paddingLeft: overhang[0], paddingRight: overhang[1] }}
    >
      {STEPS.map((step, i) => (
        <Fragment key={step.path}>
          <div className="relative shrink-0">
            <div
              className={cn(
                'flex size-6 items-center justify-center rounded-full border-2',
                i < currentStep && 'border-blue-300 bg-blue-300',
                i === currentStep && 'border-blue-300',
                i > currentStep && 'border-grey-400'
              )}
            >
              {i < currentStep && <CheckIcon className="size-3.5 text-white" />}
            </div>
            <span
              ref={i === 0 ? first : i === STEPS.length - 1 ? last : undefined}
              className={cn(
                'text-h3 absolute top-full left-1/2 mt-1 -translate-x-1/2 font-bold whitespace-nowrap',
                i <= currentStep ? 'text-blue-300' : 'text-grey-400'
              )}
            >
              {step.label}
            </span>
          </div>
          {i + 1 < STEPS.length && (
            <div
              className={cn(
                // 3px, centred on the 24px circle.
                'mt-[10.5px] h-[3px] flex-1',
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
