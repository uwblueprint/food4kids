import { type ReactNode } from 'react';

export function SubsectionHeader({ children }: { children: ReactNode }) {
  return (
    <div className="mt-10 mb-4">
      <h2 className="mb-3">{children}</h2>
      <hr className="border-grey-300" />
    </div>
  );
}
