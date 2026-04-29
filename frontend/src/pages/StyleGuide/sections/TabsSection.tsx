import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/common/components';

import { ComponentPreview } from '../components/ComponentPreview';
import { CompositionTree } from '../components/CompositionTree';
import { SectionDescription } from '../components/SectionDescription';
import { SectionHeader } from '../components/SectionHeader';
import { SectionLabel } from '../components/SectionLabel';
import { SpecNote } from '../components/SpecNote';

const TABS_TREE = `Tabs
├─ TabsList
│   └─ TabsTrigger
└─ TabsContent`;

const TABS_CODE = `import {
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from '@/common/components';

<Tabs defaultValue="tab1">
  <TabsList>
    <TabsTrigger value="tab1">Groups</TabsTrigger>
    <TabsTrigger value="tab2">Addresses</TabsTrigger>
    <TabsTrigger value="tab3">Settings</TabsTrigger>
  </TabsList>
  <TabsContent value="tab1">
    <p>Content for the Groups tab.</p>
  </TabsContent>
  <TabsContent value="tab2">
    <p>Content for the Addresses tab.</p>
  </TabsContent>
  <TabsContent value="tab3">
    <p>Content for the Settings tab.</p>
  </TabsContent>
</Tabs>`;

export function TabsSection() {
  return (
    <section className="mb-16">
      <SectionHeader>Tabs</SectionHeader>
      <SectionDescription>
        Composable tab navigation built on Radix UI Tabs. The active tab is
        tracked internally via string values — no state management required for
        uncontrolled usage.
      </SectionDescription>

      <div className="mb-10 space-y-6">
        <SpecNote title="Active Indicator">
          The active tab shows a 2px Blue/300 bottom border and bold weight text
          in Grey/500. Inactive tabs use Grey/400 with normal weight.
        </SpecNote>
        <SpecNote title="Separator">
          A full-width Grey/300 1px line is rendered below the TabsList to
          visually separate the tab bar from the content area.
        </SpecNote>
      </div>

      <SectionLabel>Composition</SectionLabel>
      <div className="mb-8">
        <CompositionTree tree={TABS_TREE} />
      </div>

      <SectionLabel>Usage</SectionLabel>
      <ComponentPreview title="Basic Tabs" code={TABS_CODE}>
        <div className="w-full max-w-lg">
          <Tabs defaultValue="tab1">
            <TabsList>
              <TabsTrigger value="tab1">Groups</TabsTrigger>
              <TabsTrigger value="tab2">Addresses</TabsTrigger>
              <TabsTrigger value="tab3">Settings</TabsTrigger>
            </TabsList>
            <TabsContent value="tab1" className="pt-6">
              <p className="text-p2 text-grey-500">
                Content for the <strong>Groups</strong> tab.
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
      </ComponentPreview>
    </section>
  );
}
