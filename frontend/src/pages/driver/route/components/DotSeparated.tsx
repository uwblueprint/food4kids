import { Fragment, type ReactNode } from 'react';

import { cn } from '@/lib/utils';

export interface DotSeparatedProps {
  /** Falsy entries are dropped, so an absent field doesn't leave a stray dot. */
  items: ReactNode[];
  className?: string;
}

/**
 * Facts joined by the design's separator: a 3px dot with 6px either side,
 * inking in the current text colour.
 *
 * Not a "·" between spaces — that renders ~3px narrower than the frames and
 * drags everything after it left. It also reads the character out loud; the
 * dot here is decorative, so it's hidden from assistive tech.
 */
export function DotSeparated({ items, className }: DotSeparatedProps) {
  const shown = items.filter(Boolean);
  return (
    <span className={cn('flex items-center gap-1.5', className)}>
      {shown.map((item, i) => (
        <Fragment key={i}>
          {i > 0 && (
            <span
              aria-hidden="true"
              className="size-[3px] shrink-0 rounded-full bg-current"
            />
          )}
          {item}
        </Fragment>
      ))}
    </span>
  );
}
