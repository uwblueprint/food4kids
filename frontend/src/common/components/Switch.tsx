import { Switch as SwitchPrimitive } from 'radix-ui';
import * as React from 'react';

import { cn } from '@/lib/utils';

/**
 * Pill toggle for an on/off setting.
 *
 * Distinct from {@link Checkbox}-style inputs: this commits its change as soon
 * as it is flipped, so it belongs on settings that read as state rather than on
 * form fields awaiting a submit.
 */
function Switch({
  className,
  ...props
}: React.ComponentProps<typeof SwitchPrimitive.Root>) {
  return (
    <SwitchPrimitive.Root
      data-slot="switch"
      className={cn(
        'peer inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full',
        'outline outline-1 outline-offset-[-1px] transition-colors',
        'data-[state=checked]:bg-blue-300 data-[state=checked]:outline-blue-300',
        'data-[state=unchecked]:bg-grey-300 data-[state=unchecked]:outline-grey-300',
        'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-300',
        'disabled:cursor-not-allowed disabled:opacity-60',
        className
      )}
      {...props}
    >
      <SwitchPrimitive.Thumb
        data-slot="switch-thumb"
        className={cn(
          'bg-grey-100 pointer-events-none block size-5 rounded-full shadow-sm',
          'transition-transform data-[state=checked]:translate-x-[22px]',
          'data-[state=unchecked]:translate-x-0.5'
        )}
      />
    </SwitchPrimitive.Root>
  );
}

export { Switch };
