import { forwardRef, type InputHTMLAttributes } from 'react';

import { cn } from '@/lib/utils';

const Input = forwardRef<
  HTMLInputElement,
  InputHTMLAttributes<HTMLInputElement>
>(({ className, type, ...props }, ref) => {
  return (
    <input
      ref={ref}
      type={type}
      className={cn(
        'text-p2 text-grey-500 placeholder:text-p1 placeholder:text-grey-400',
        'w-full rounded-lg px-6 py-3',
        'transition-colors',
        'bg-grey-100 outline-grey-300 outline outline-1 outline-offset-[-1px]',
        'focus:outline-2 focus:outline-blue-300',
        'disabled:bg-grey-150 disabled:text-grey-400 disabled:cursor-not-allowed disabled:opacity-60',
        className
      )}
      {...props}
    />
  );
});

Input.displayName = 'Input';

export { Input };
