import { type ReactNode } from 'react';

export function SectionHeader({ children }: { children: ReactNode }) {
  return (
    <>
      <h2 className="mb-1">{children}</h2>
      <hr className="border-grey-300 mb-6" />
    </>
  );
}
