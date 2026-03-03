import { cva, type VariantProps } from 'class-variance-authority';
import { Slot } from 'radix-ui';
import * as React from 'react';

import { cn } from '@/lib/utils';

const buttonVariants = cva(
  /* ---- shared base ---- */
  [
    'inline-flex items-center justify-center gap-2',
    'transition-colors duration-150 ease-in-out',
    'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-300',
    'disabled:pointer-events-none disabled:opacity-50',
    'cursor-pointer',
    '[&_svg]:pointer-events-none [&_svg]:shrink-0',
  ],
  {
    variants: {
      variant: {
        primary: 'bg-blue-300 text-grey-100 hover:bg-blue-400',
        secondary:
          'bg-grey-200 text-grey-500 border border-grey-300 hover:bg-grey-300',
        tertiary: 'bg-grey-100 text-grey-500 border border-grey-300',
        textLink: 'bg-transparent text-blue-300 hover:underline',
      },
      shape: {
        default: [
          'font-nunito text-h3',
          'h-[44px] min-w-[104px] px-6 rounded-[40px]',
          'w-full md:w-auto',
        ],
        circular: 'size-[44px] rounded-full',
      },
    },
    compoundVariants: [
      /* textLink doesn't need pill sizing — reset padding, width, and radius */
      {
        variant: 'textLink',
        shape: 'default',
        className: 'min-w-0 px-0 rounded-none w-auto h-auto',
      },
    ],
    defaultVariants: {
      variant: 'primary',
      shape: 'default',
    },
  }
);

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

export { Button, buttonVariants };
