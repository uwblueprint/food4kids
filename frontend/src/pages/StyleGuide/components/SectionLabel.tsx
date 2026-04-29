import { type ReactNode } from 'react';

import { cn } from '@/lib/utils';

export function SectionLabel({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <p
      className={cn(
        'text-p3 mb-2 font-semibold tracking-wider text-grey-400 uppercase',
        className,
      )}
    >
      {children}
    </p>
  );
}
