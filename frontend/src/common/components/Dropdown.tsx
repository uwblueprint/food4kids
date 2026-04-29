import * as SelectPrimitive from '@radix-ui/react-select';

import ChevronDown from '@/assets/icons/chevron-down.svg?react';
import { cn } from '@/lib/utils';

const Dropdown = SelectPrimitive.Root;
const DropdownValue = SelectPrimitive.Value;
const DropdownGroup = SelectPrimitive.Group;

function DropdownTrigger({
  className,
  children,
  ...props
}: React.ComponentProps<typeof SelectPrimitive.Trigger>) {
  return (
    <SelectPrimitive.Trigger
      className={cn(
        'inline-flex w-full cursor-pointer items-center justify-between rounded-full px-6 py-3',
        'text-p2 text-grey-500 outline-none transition-colors',
        'bg-grey-100 ring-1 ring-grey-300',
        'focus:ring-2 focus:ring-blue-300',
        'data-[state=open]:ring-2 data-[state=open]:ring-blue-300',
        'data-[placeholder]:text-grey-400',
        'disabled:bg-grey-150 disabled:cursor-not-allowed disabled:opacity-60',
        className,
      )}
      {...props}
    >
      {children}
      <SelectPrimitive.Icon className="ml-2 shrink-0">
        <ChevronDown className="h-4 w-4 text-grey-500" />
      </SelectPrimitive.Icon>
    </SelectPrimitive.Trigger>
  );
}

function DropdownContent({
  className,
  children,
  ...props
}: React.ComponentProps<typeof SelectPrimitive.Content>) {
  return (
    <SelectPrimitive.Portal>
      <SelectPrimitive.Content
        position="popper"
        sideOffset={4}
        className={cn(
          'z-50 w-[var(--radix-select-trigger-width)] overflow-hidden rounded-lg',
          'border border-grey-300 bg-grey-100 shadow-card',
          'data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:zoom-in-95',
          'data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95',
          className,
        )}
        {...props}
      >
        <SelectPrimitive.Viewport className="p-3">
          {children}
        </SelectPrimitive.Viewport>
      </SelectPrimitive.Content>
    </SelectPrimitive.Portal>
  );
}

function DropdownItem({
  className,
  children,
  ...props
}: React.ComponentProps<typeof SelectPrimitive.Item>) {
  return (
    <SelectPrimitive.Item
      className={cn(
        'relative flex w-full cursor-pointer select-none items-center rounded-md px-3 py-2',
        'text-p1 text-grey-500 outline-none',
        'hover:bg-blue-50 focus:bg-blue-50',
        'data-[state=checked]:font-semibold data-[state=checked]:text-blue-300',
        className,
      )}
      {...props}
    >
      <SelectPrimitive.ItemText>{children}</SelectPrimitive.ItemText>
    </SelectPrimitive.Item>
  );
}

export { Dropdown, DropdownContent, DropdownGroup,DropdownItem, DropdownTrigger, DropdownValue };
