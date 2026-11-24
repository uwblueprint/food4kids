import { useLayoutEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';

/** Returns a ref for a scroll container (e.g. AdminLayout's `<main>`) that resets to the top on route change. */
export function useRouteScrollReset() {
  const scrollRef = useRef<HTMLElement>(null);
  const { pathname } = useLocation();

  useLayoutEffect(() => {
    scrollRef.current?.scrollTo({
      top: 0,
      behavior: 'instant',
    });
  }, [pathname]);

  return scrollRef;
}
