import * as React from 'react';

import { cn } from '@/lib/utils';

function Card({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'shadow-card flex flex-col justify-between rounded-2xl bg-white',
        'pt-6 pr-8 pb-8 pl-8',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export { Card };
