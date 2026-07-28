import { Tabs as TabsPrimitive } from 'radix-ui';
import * as React from 'react';

import { cn } from '@/lib/utils';

function Tabs({ ...props }: React.ComponentProps<typeof TabsPrimitive.Root>) {
  return <TabsPrimitive.Root data-slot="tabs" {...props} />;
}

function TabsList({
  className,
  ...props
}: React.ComponentProps<typeof TabsPrimitive.List>) {
  return (
    // 40px between the divider and whatever the tab reveals, per the design.
    <div className="mb-10 flex flex-col gap-0">
      <TabsPrimitive.List
        data-slot="tabs-list"
        // gap-13 (52px) is the 53px the design leaves between labels, to the
        // nearest spacing step.
        className={cn('flex gap-13', className)}
        {...props}
      />
      <hr className="border-grey-300" />
    </div>
  );
}

function TabsTrigger({
  className,
  ...props
}: React.ComponentProps<typeof TabsPrimitive.Trigger>) {
  return (
    <TabsPrimitive.Trigger
      data-slot="tabs-trigger"
      // Per the Figma (measured on the Groups/Routes/Addresses frames, each
      // showing a different tab active): labels are Nunito Bold 20/28 — the
      // Desktop/H2 style — and every label is grey-500 whatever its state. The
      // active tab is marked by its 3px blue underline alone, not by colour.
      className={cn(
        'text-h2 font-nunito cursor-pointer pb-1 font-bold capitalize',
        'text-grey-500 transition-colors',
        'data-[state=active]:border-b-[3px] data-[state=active]:border-blue-300',
        className
      )}
      {...props}
    />
  );
}

function TabsContent({
  className,
  ...props
}: React.ComponentProps<typeof TabsPrimitive.Content>) {
  return (
    <TabsPrimitive.Content
      data-slot="tabs-content"
      className={cn(className)}
      {...props}
    />
  );
}

export { Tabs, TabsContent, TabsList, TabsTrigger };
