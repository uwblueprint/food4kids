import { cva, type VariantProps } from 'class-variance-authority';
import * as React from 'react';

import { cn } from '@/lib/utils';

const bannerVariants = cva(
  'flex items-start gap-2.5 rounded-2xl border px-4 py-6',
  {
    variants: {
      variant: {
        success: 'border-success-stroke bg-success-fill',
        error: 'bg-light-red border-red',
        warning: 'border-dark-yellow bg-light-yellow',
      },
    },
    defaultVariants: {
      variant: 'success',
    },
  }
);

const iconChar = {
  success: '\u2713',
  error: '\u26A0',
  warning: '\u26A0',
} as const;

const iconClass = {
  success: 'text-success-stroke',
  error: 'text-red',
  warning: 'text-dark-yellow',
} as const;

const textClass = {
  success: 'text-success-stroke font-semibold',
  error: 'text-p2 text-red font-semibold',
  warning: 'text-p2 text-dark-yellow font-semibold',
} as const;

const subtitleClass = {
  success: 'text-p2 text-success-stroke opacity-80',
  error: 'text-p2 text-red opacity-80',
  warning: 'text-p2 text-dark-yellow opacity-80',
} as const;

type BannerVariant = keyof typeof iconChar;

interface BannerProps
  extends
    React.HTMLAttributes<HTMLDivElement>,
    Omit<VariantProps<typeof bannerVariants>, 'variant'> {
  variant: BannerVariant;
  subtitle?: React.ReactNode;
}

function Banner({
  variant = 'success',
  subtitle,
  className,
  children,
  ...props
}: BannerProps) {
  return (
    <div className={cn(bannerVariants({ variant }), className)} {...props}>
      <span className={iconClass[variant]}>{iconChar[variant]}</span>
      <div>
        <p className={textClass[variant]}>{children}</p>
        {subtitle && <p className={subtitleClass[variant]}>{subtitle}</p>}
      </div>
    </div>
  );
}

export { Banner };
