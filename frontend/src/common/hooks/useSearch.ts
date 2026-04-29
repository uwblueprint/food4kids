import { type ChangeEvent, useState } from 'react';

export interface UseSearchReturn {
  value: string;
  onChange: (e: ChangeEvent<HTMLInputElement>) => void;
}

export function useSearch(initialValue = ''): UseSearchReturn {
  const [value, setValue] = useState(initialValue);
  return {
    value,
    onChange: (e) => setValue(e.target.value),
  };
}
