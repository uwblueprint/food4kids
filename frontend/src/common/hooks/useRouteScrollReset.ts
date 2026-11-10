import { useLayoutEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';

export function useRouteScrollReset() {
  const scrollRef = useRef<HTMLDivElement>(null);
  const { pathname } = useLocation();

  useLayoutEffect(() => {
    scrollRef.current?.scrollTo({
      top: 0,
      behavior: 'instant',
    });
  }, [pathname]);

  return scrollRef;
}
