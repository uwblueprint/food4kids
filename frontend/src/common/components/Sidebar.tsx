import * as React from 'react';
import { NavLink } from 'react-router-dom';

import { cn } from '@/lib/utils';

function SidebarProvider({ children }: { children: React.ReactNode }) {
  return <div className="flex h-screen overflow-hidden">{children}</div>;
}

// ---------------------------------------------------------------------------
// Sidebar panel
// ---------------------------------------------------------------------------

function Sidebar({ className, children }: React.ComponentProps<'aside'>) {
  return (
    <aside
      className={cn(
        // 120px rail, 24px above the logo and 48px below it — the Web-Nav-Bar
        // component's own measurements.
        'flex w-30 shrink-0 flex-col items-center gap-12 bg-white px-4 py-6',
        'shadow-[0px_0px_32px_0px_rgba(0,0,0,0.04)]',
        'z-10 h-full',
        className
      )}
    >
      {children}
    </aside>
  );
}

// ---------------------------------------------------------------------------
// Sidebar regions
// ---------------------------------------------------------------------------

function SidebarHeader({ className, children }: React.ComponentProps<'div'>) {
  return (
    <div className={cn('flex w-full flex-col items-center', className)}>
      {children}
    </div>
  );
}

function SidebarContent({ className, children }: React.ComponentProps<'div'>) {
  return (
    <div
      className={cn(
        'flex flex-1 flex-col items-center gap-2 overflow-y-auto',
        className
      )}
    >
      {children}
    </div>
  );
}

function SidebarFooter({ className, children }: React.ComponentProps<'div'>) {
  return (
    <div className={cn('flex w-full flex-col items-center', className)}>
      {children}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Menu
// ---------------------------------------------------------------------------

function SidebarMenu({ className, children }: React.ComponentProps<'nav'>) {
  return (
    // 48px between items, per the design. They sit in a column from the top
    // rather than spreading to fill the rail.
    <nav className={cn('flex flex-col items-center gap-12', className)}>
      {children}
    </nav>
  );
}

interface SidebarMenuItemProps {
  label: string;
  to: string;
  icon: React.FC<React.SVGProps<SVGSVGElement>>;
  /**
   * The icon's own size, for the ones whose artwork isn't square — `size-6`
   * would stretch them. The 24px box around it stays either way, so the
   * labels below keep their line.
   */
  iconClassName?: string;
  end?: boolean;
}

function SidebarMenuItem({
  label,
  to,
  icon: Icon,
  iconClassName = 'size-6',
  end = false,
}: SidebarMenuItemProps) {
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        cn(
          // 80x80: 14px padding, a 24px icon, 4px, then a 16/24 label. The
          // label carries its own size, so the box does not set one.
          'flex w-20 flex-col items-center justify-center gap-1 rounded-xl px-4 py-3.5',
          'transition-colors',
          isActive
            ? 'bg-blue-50 text-blue-400 shadow-[0px_4px_24px_0px_rgba(0,0,0,0.08)] outline outline-1 outline-offset-[-1px] outline-blue-100'
            : 'text-grey-500 hover:bg-grey-150'
        )
      }
    >
      <span className="flex size-6 items-center justify-center">
        <Icon className={iconClassName} />
      </span>
      <span className="text-p1 text-center">{label}</span>
    </NavLink>
  );
}

// ---------------------------------------------------------------------------
// Inset (main content area)
// ---------------------------------------------------------------------------

function SidebarInset({ className, children }: React.ComponentProps<'main'>) {
  return (
    <main className={cn('bg-grey-200 flex-1 overflow-y-auto', className)}>
      {children}
    </main>
  );
}

// ---------------------------------------------------------------------------
// Trigger (future use)
// ---------------------------------------------------------------------------

function SidebarTrigger({
  className,
  ...props
}: React.ComponentProps<'button'>) {
  return (
    <button
      type="button"
      className={cn('cursor-pointer', className)}
      {...props}
    />
  );
}

export {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarInset,
  SidebarMenu,
  SidebarMenuItem,
  SidebarProvider,
  SidebarTrigger,
};
