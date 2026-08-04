import { useCallback, useEffect, useRef } from 'react';

const FIFTEEN_MINUTES = 15 * 60 * 1000;

interface UseInactivityTimeoutOptions {
  onTimeout: () => void;
  enabled: boolean;
  timeoutMs?: number;
}

export function useInactivityTimeout({
  onTimeout,
  enabled,
  timeoutMs = FIFTEEN_MINUTES,
}: UseInactivityTimeoutOptions) {
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const resetTimer = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }
    timerRef.current = setTimeout(() => {
      onTimeout();
    }, timeoutMs);
  }, [onTimeout, timeoutMs]);

  useEffect(() => {
    if (!enabled) return;

    const events = ['mousemove', 'keydown', 'click', 'scroll', 'touchstart'];

    // Hundreds of events may fire in a second, so we pause for a second before detecting the next event
    let throttleTimeout: ReturnType<typeof setTimeout> | null = null;
    const handleUserActivity = () => {
      if (!throttleTimeout) {
        resetTimer();
        throttleTimeout = setTimeout(() => {
          throttleTimeout = null;
        }, 1000);
      }
    };

    // Set initial timer when enabled
    resetTimer();

    // Attach activity listeners
    events.forEach((event) => {
      window.addEventListener(event, handleUserActivity);
    });

    // Clean up timers and event listeners
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
      if (throttleTimeout) clearTimeout(throttleTimeout);
      events.forEach((event) => {
        window.removeEventListener(event, handleUserActivity);
      });
    };
  }, [enabled, resetTimer]);
}
