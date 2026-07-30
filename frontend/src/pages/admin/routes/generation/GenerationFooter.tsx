import type { ReactNode } from 'react';

/**
 * The wizard's sticky action bar: an 84px full-bleed strip pinned to the
 * bottom of the viewport, holding the back/continue pair.
 *
 * Full-bleed means it has to cancel the page margins that wrap every admin
 * route — hence the negative insets, which are the `.admin-page-margins`
 * values inverted. Its own padding then puts the buttons back on the content
 * grid, so they line up with the tables above.
 */
export function GenerationFooter({ children }: { children: ReactNode }) {
  return (
    <div className="border-grey-300 bg-grey-200 tablet:-mx-10 tablet:px-10 desktop:-mx-12 desktop:px-12 sticky bottom-0 z-20 -mx-5 mt-auto -mb-6 flex h-21 items-center justify-between gap-4 border-t px-5 py-5">
      {children}
    </div>
  );
}
