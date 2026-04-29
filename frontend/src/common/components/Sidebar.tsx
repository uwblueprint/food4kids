import * as React from 'react';
import { NavLink } from 'react-router-dom';

import { cn } from '@/lib/utils';

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------

interface SidebarContextValue {
  // placeholder for future collapsible state
}

const SidebarContext = React.createContext<SidebarContextValue>({});

function SidebarProvider({ children }: { children: React.ReactNode }) {
  return (
    <SidebarContext.Provider value={{}}>
      <div className="flex h-screen overflow-hidden">{children}</div>
    </SidebarContext.Provider>
  );
}

// ---------------------------------------------------------------------------
// Sidebar panel
// ---------------------------------------------------------------------------

function Sidebar({ className, children }: React.ComponentProps<'aside'>) {
  return (
    <aside
      className={cn(
        'flex w-28 shrink-0 flex-col items-center gap-12 bg-white px-4 py-6',
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
    <nav className={cn('flex flex-col items-center gap-2', className)}>
      {children}
    </nav>
  );
}

interface SidebarMenuItemProps {
  label: string;
  to: string;
  icon: React.FC<React.SVGProps<SVGSVGElement>>;
  end?: boolean;
}

function SidebarMenuItem({
  label,
  to,
  icon: Icon,
  end = false,
}: SidebarMenuItemProps) {
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        cn(
          'flex w-20 flex-col items-center justify-center gap-1 rounded-2xl px-4 py-3.5',
          'text-base transition-colors',
          isActive
            ? 'bg-blue-50 text-blue-400 shadow-[0px_4px_24px_0px_rgba(0,0,0,0.08)] outline outline-1 outline-offset-[-1px] outline-blue-100'
            : 'text-grey-500 hover:bg-grey-150'
        )
      }
    >
      <Icon className="size-6" />
      <span className="text-center text-sm leading-tight">{label}</span>
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
