import { cva, type VariantProps } from 'class-variance-authority';
import * as React from 'react';

import { cn } from '@/lib/utils';

const tagVariants = cva('inline-flex items-center gap-2.5', {
  variants: {
    variant: {
      success:
        'h-8 rounded-lg border px-4 py-1.5 font-bold border-success-stroke bg-success-fill text-success-stroke',
      error:
        'h-8 rounded-lg border px-4 py-1.5 font-bold bg-light-red border-red text-red',
      primary: 'rounded-[30px] px-2 py-0.5 text-p3 bg-blue-50 text-blue-300',
      secondary:
        'rounded-[30px] px-2 py-0.5 text-p3 bg-grey-100 text-grey-400 outline outline-1 outline-offset-[-1px] outline-grey-300',
    },
  },
  defaultVariants: {
    variant: 'success',
  },
});

type TagVariant = 'success' | 'error' | 'primary' | 'secondary';

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
