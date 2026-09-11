import { useState } from 'react';

import { PopupContainerContext } from './PopupHost.context';

/**
 * Hosts popover panels inside the surrounding scroll context instead of
 * document.body. Radix panels are `position: fixed` and repositioned from JS,
 * which trails compositor-driven scrolling by a frame; `translateZ(0)` makes
 * this in-flow div their containing block, so the compositor moves them with
 * the content and no JS runs in the scroll loop. Place it directly inside a
 * `relative` element that scrolls with the page content.
 */
export function PopupHost({ children }: { children: React.ReactNode }) {
  const [container, setContainer] = useState<HTMLDivElement | null>(null);
  return (
    <PopupContainerContext.Provider value={container}>
      {children}
      <div
        ref={setContainer}
        className="absolute top-0 left-0 z-50 [transform:translateZ(0)]"
      />
    </PopupContainerContext.Provider>
  );
}
