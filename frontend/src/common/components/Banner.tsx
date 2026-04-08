import { cva, type VariantProps } from 'class-variance-authority';
import { type ReactNode } from 'react';

import AlertCircleIcon from '@/assets/icons/alert-circle.svg?react';
import AlertTriangleIcon from '@/assets/icons/alert-triangle.svg?react';
import CheckCircleIcon from '@/assets/icons/check-circle.svg?react';
import { cn } from '@/lib/utils';

const bannerVariants = cva(
  'flex items-center gap-2.5 rounded-2xl border px-4 py-4',
  {
    variants: {
      variant: {
        error: 'bg-light-red border-red',
        warning: 'border-dark-yellow bg-light-yellow',
        success: 'border-success-stroke bg-success-fill',
      },
    },
    defaultVariants: {
      variant: 'error',
    },
  }
);

const iconClass: Record<string, string> = {
  error: 'text-red',
  warning: 'text-dark-yellow',
  success: 'text-success-stroke',
};

const textClass: Record<string, string> = {
  error: 'text-red',
  warning: 'text-dark-yellow',
  success: 'text-success-stroke',
};

const Icon = ({ variant }: { variant: string }) => {
  const cls = cn(iconClass[variant], 'size-5 shrink-0');
  if (variant === 'success') return <CheckCircleIcon className={cls} />;
  if (variant === 'warning') return <AlertTriangleIcon className={cls} />;
  return <AlertCircleIcon className={cls} />;
};

interface BannerProps extends VariantProps<typeof bannerVariants> {
  variant: 'error' | 'warning' | 'success';
  children: ReactNode;
  className?: string;
}

export const Banner = ({
  variant = 'error',
  children,
  className,
}: BannerProps) => {
  return (
    <div className={cn(bannerVariants({ variant }), className)}>
      <Icon variant={variant} />
      <p className={cn('text-p2 font-semibold', textClass[variant])}>
        {children}
      </p>
    </div>
  );
};
