import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/common/components';

import { SectionHeader } from '../components/SectionHeader';
import { SpecNote } from '../components/SpecNote';

export function TabsSection() {
  return (
    <section className="mb-16">
      <SectionHeader>Tabs</SectionHeader>

      <div className="mb-10 space-y-6">
        <SpecNote title="Composition">
          Built on Radix UI Tabs with a composable API: Tabs › TabsList ›
          TabsTrigger, and TabsContent. Active state is tracked by Radix
          internally via string values.
        </SpecNote>

        <SpecNote title="Active Indicator">
          The active tab shows a 2px Blue/300 bottom border and Bold weight text
          in Grey/500. Inactive tabs use Grey/400 with normal weight.
        </SpecNote>

        <SpecNote title="Separator">
          A full-width Grey/300 1px line is rendered below the TabsList to
          visually separate the tab bar from the content area.
        </SpecNote>
      </div>

      <div className="border-grey-300 bg-grey-150 overflow-hidden rounded-xl border p-6">
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Groups</TabsTrigger>
            <TabsTrigger value="tab2">Addresses</TabsTrigger>
            <TabsTrigger value="tab3">Settings</TabsTrigger>
          </TabsList>

          <TabsContent value="tab1" className="pt-6">
            <p className="text-p2 text-grey-500">
              Content for the <strong>Groups</strong> tab. Switch tabs above to
              see the active indicator move.
            </p>
          </TabsContent>

          <TabsContent value="tab2" className="pt-6">
            <p className="text-p2 text-grey-500">
              Content for the <strong>Addresses</strong> tab.
            </p>
          </TabsContent>

          <TabsContent value="tab3" className="pt-6">
            <p className="text-p2 text-grey-500">
              Content for the <strong>Settings</strong> tab.
            </p>
          </TabsContent>
        </Tabs>
      </div>
    </section>
  );
}
