import { type ReactNode } from 'react';

import { cn } from '@/lib/utils';

export function SectionHeader({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn('mb-6', className)}>
      <h2 className="mb-1">{children}</h2>
      <hr className="border-grey-300" />
    </div>
  );
}
