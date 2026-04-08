import { cva, type VariantProps } from 'class-variance-authority';
import { type HTMLAttributes, type ReactNode } from 'react';

import { cn } from '@/lib/utils';

const badgeVariants = cva(
  'inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-p3 font-semibold',
  {
    variants: {
      variant: {
        success: 'border-success-stroke bg-success-fill text-success-stroke',
        error: 'border-red bg-light-red text-red',
        warning: 'border-dark-yellow bg-light-yellow text-dark-yellow',
        default: 'border-grey-300 bg-grey-150 text-grey-500',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
);

interface BadgeProps
  extends HTMLAttributes<HTMLSpanElement>, VariantProps<typeof badgeVariants> {
  variant: 'success' | 'error' | 'warning' | 'default';
  children: ReactNode;
}

export const Badge = ({
  variant,
  children,
  className,
  ...props
}: BadgeProps) => {
  return (
    <span className={cn(badgeVariants({ variant }), className)} {...props}>
      {children}
    </span>
  );
};
