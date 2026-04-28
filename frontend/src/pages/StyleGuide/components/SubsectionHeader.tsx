import { type ReactNode } from 'react';

export function SubsectionHeader({ children }: { children: ReactNode }) {
  return (
    <>
      <h3 className="mt-10 mb-1">{children}</h3>
      <hr className="border-grey-300 mb-6" />
    </>
  );
}
