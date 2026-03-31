import { type ReactNode } from 'react';

export function SpecNote({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <div>
      <p className="text-p3 mb-1 font-semibold tracking-wider text-blue-300 uppercase">
        {title}
      </p>
      <p className="text-p1 text-grey-500">{children}</p>
    </div>
  );
}
