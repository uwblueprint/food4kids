import { Fragment, useLayoutEffect, useRef, useState } from 'react';

import CheckIcon from '@/assets/icons/check.svg?react';
import { cn } from '@/lib/utils';

/** Half the 24px circle, in px — the label overhang is measured against it. */
const CIRCLE_RADIUS = 12;

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
  const firstLabel = useRef<HTMLSpanElement>(null);
  const lastLabel = useRef<HTMLSpanElement>(null);
  // Half of each end label hangs off its circle. The frames put those two
  // labels flush with the page margins, so the row is inset by exactly that
  // overhang — measured, because it's the rendered text width that decides it,
  // and a hardcoded inset is both wrong for one end and silently wrong again
  // the next time a label's wording changes.
  const [endInset, setEndInset] = useState({ left: 0, right: 0 });

  useLayoutEffect(() => {
    const first = firstLabel.current;
    const last = lastLabel.current;
    if (!first || !last) return;

    // getBoundingClientRect, not offsetWidth: the latter rounds to whole
    // pixels, which leaves the end labels a couple of px off the margin.
    const overhang = (label: HTMLSpanElement) =>
      Math.max(0, label.getBoundingClientRect().width / 2 - CIRCLE_RADIUS);
    const measure = () =>
      setEndInset({ left: overhang(first), right: overhang(last) });

    measure();
    // A layout effect runs before the web font has necessarily swapped in, and
    // fallback metrics put the inset a couple of px out, so re-measure once the
    // real font is in. The observer then keeps up with anything later — a
    // wording change, a zoom, a font-size change at another breakpoint.
    void document.fonts.ready.then(measure);
    const observer = new ResizeObserver(measure);
    observer.observe(first);
    observer.observe(last);
    return () => observer.disconnect();
  }, []);

  return (
    // The circles are evenly spaced and the labels hang off them: each label is
    // centred on its circle and taken out of the flow, so a label as wide as
    // "Edit Route Groups" doesn't push its circle around. That leaves the row as
    // fixed-size circles with the connectors splitting whatever is left over.
    // `pb-6` reserves the 4px gap + 20px line the labels occupy.
    <div
      className={cn('flex w-full items-center pb-6', className)}
      style={{ paddingLeft: endInset.left, paddingRight: endInset.right }}
    >
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
              ref={
                i === 0
                  ? firstLabel
                  : i === STEPS.length - 1
                    ? lastLabel
                    : undefined
              }
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
