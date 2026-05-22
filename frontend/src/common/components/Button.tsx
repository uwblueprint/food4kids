import { type VariantProps } from 'class-variance-authority';
import { Slot } from 'radix-ui';
import * as React from 'react';

import { cn } from '@/lib/utils';

import { buttonVariants } from './Button.variants';

function Button({
  className,
  variant = 'primary',
  shape = 'default',
  asChild = false,
  ...props
}: React.ComponentProps<'button'> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean;
  }) {
  const Comp = asChild ? Slot.Root : 'button';

  return (
    <Comp
      data-slot="button"
      data-variant={variant}
      data-shape={shape}
      className={cn(buttonVariants({ variant, shape, className }))}
      {...props}
    />
  );
}

export { Button };
