import { type ReactNode } from 'react';

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}

function AccountSection() {
  // TODO: fetch account from global context? (name, role, avatar, or initials as profile)

  return (
    <div className="flex items-center gap-4">
      <div className="bg-brand-pink flex size-10 items-center justify-center rounded-full">
        <span className="text-p2 text-grey-100">EL</span>
      </div>
      <div className="inline-flex flex-col items-start">
        <p className="text-p1 font-medium">Emily Loro</p>
        <p className="text-p2 text-grey-400">Admin</p>
      </div>
    </div>
  );
}

export function PageHeader({ title, subtitle, actions }: PageHeaderProps) {
  return (
    <div className="flex items-start justify-between">
      <div className="flex flex-col items-start">
        <h1>{title}</h1>
        {subtitle && <p className="text-p1 text-grey-400">{subtitle}</p>}
      </div>

      <div className="flex items-center gap-6">
        {actions && actions}
        <AccountSection />
      </div>
    </div>
  );
}
