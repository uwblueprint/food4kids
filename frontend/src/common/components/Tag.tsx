import { cva, type VariantProps } from 'class-variance-authority';
import * as React from 'react';

import { cn } from '@/lib/utils';

const tagVariants = cva(
  'inline-flex h-8 items-center gap-2.5 rounded-lg border px-4 py-1.5 font-nunito font-bold',
  {
    variants: {
      variant: {
        success: 'border-success-stroke bg-success-fill text-success-stroke',
      },
    },
    defaultVariants: {
      variant: 'success',
    },
  }
);

type TagVariant = 'success';

interface TagProps
  extends
    React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof tagVariants> {
  variant: TagVariant;
  onRemove?: () => void;
}

function Tag({
  variant = 'success',
  onRemove,
  className,
  children,
  ...props
}: TagProps) {
  return (
    <span className={cn(tagVariants({ variant }), className)} {...props}>
      {children}
      {onRemove && (
        <button
          type="button"
          onClick={onRemove}
          aria-label="Remove"
          className="cursor-pointer leading-none opacity-70 hover:opacity-100"
        >
          &#10005;
        </button>
      )}
    </span>
  );
}

export { Tag };
