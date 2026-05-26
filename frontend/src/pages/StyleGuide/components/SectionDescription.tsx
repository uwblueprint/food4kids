import { type ReactNode } from 'react';

export function SectionDescription({ children }: { children: ReactNode }) {
  return <p className="text-p1 text-grey-400 mb-6">{children}</p>;
}
