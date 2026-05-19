import { cva, type VariantProps } from 'class-variance-authority';
import * as React from 'react';

import AlertCircleIcon from '@/assets/icons/alert-circle.svg?react';
import AlertTriangleIcon from '@/assets/icons/alert-triangle.svg?react';
import CheckCircleIcon from '@/assets/icons/check-circle.svg?react';
import XIcon from '@/assets/icons/x.svg?react';
import { cn } from '@/lib/utils';

const bannerVariants = cva('flex items-start gap-4 rounded-2xl border p-6', {
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
});

const IconComponent = {
  success: CheckCircleIcon,
  error: AlertCircleIcon,
  warning: AlertTriangleIcon,
} as const;

const iconClass = {
  success: 'shrink-0 size-[18px] text-success-stroke',
  error: 'shrink-0 size-[18px] text-red',
  warning: 'shrink-0 size-[18px] text-dark-yellow',
} as const;

const textClass = {
  success: 'text-p1',
  error: 'text-p1 text-grey-500',
  warning: 'text-p1 text-grey-500',
} as const;

const subtitleClass = {
  success: 'text-p2 opacity-80',
  error: 'text-p2 text-grey-500 opacity-80',
  warning: 'text-p2 text-grey-500 opacity-80',
} as const;

type BannerVariant = keyof typeof IconComponent;

interface BannerProps
  extends
    React.HTMLAttributes<HTMLDivElement>,
    Omit<VariantProps<typeof bannerVariants>, 'variant'> {
  variant: BannerVariant;
  subtitle?: React.ReactNode;
  onDismiss?: () => void;
}

function Banner({
  variant = 'success',
  subtitle,
  onDismiss,
  className,
  children,
  ...props
}: BannerProps) {
  const Icon = IconComponent[variant];
  return (
    <div className={cn(bannerVariants({ variant }), className)} {...props}>
      <Icon className={iconClass[variant]} />
      <div className="min-w-0 flex-1">
        <p className={textClass[variant]}>{children}</p>
        {subtitle && (
          <p className={cn(subtitleClass[variant], 'mt-1')}>{subtitle}</p>
        )}
      </div>
      {onDismiss && (
        <button
          type="button"
          onClick={onDismiss}
          aria-label="Dismiss"
          className="text-grey-400 hover:text-grey-500 shrink-0 transition-colors"
        >
          <XIcon className="size-5" />
        </button>
      )}
    </div>
  );
}

export { Banner };
