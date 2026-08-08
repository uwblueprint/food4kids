import { useEffect, useState } from 'react';

/**
 * Returns a copy of `value` that only updates after it has stopped changing
 * for `delayMs`. Used to debounce search input so a server query fires once
 * the user pauses typing rather than on every keystroke.
 */
export function useDebouncedValue<T>(value: T, delayMs = 300): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(timer);
  }, [value, delayMs]);

  return debounced;
}
