import { cn } from '@/lib/utils';

interface SpinnerProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

const sizeClasses = {
  sm: 'size-8 border-[4px]',
  md: 'size-12 border-[5px]',
  lg: 'size-16 border-[6px]',
};

function Spinner({ className, size = 'lg' }: SpinnerProps) {
  return (
    <div
      role="status"
      aria-label="Loading"
      className={cn(
        'rounded-full animate-spin',
        'border-grey-300 border-t-blue-300',
        sizeClasses[size],
        className
      )}
    />
  );
}

export { Spinner };
