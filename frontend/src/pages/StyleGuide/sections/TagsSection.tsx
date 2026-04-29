import { Tag } from '@/common/components';

import { ComponentPreview } from '../components/ComponentPreview';
import { SectionDescription } from '../components/SectionDescription';
import { SectionHeader } from '../components/SectionHeader';

const TAG_STATUS_CODE = `import { Tag } from '@/common/components';

<div className="flex gap-3">
  <Tag variant="success">DeliveriesData.xlsx</Tag>
  <Tag variant="success" onRemove={() => {}}>
    DeliveriesData.xlsx
  </Tag>
  <Tag variant="error">Missing Address</Tag>
</div>`;

const TAG_STATE_CODE = `import { Tag } from '@/common/components';

<div className="flex gap-3">
  <Tag variant="primary">New</Tag>
  <Tag variant="secondary">Edited</Tag>
</div>`;

export function TagsSection() {
  return (
    <section className="mb-16">
      <SectionHeader>Tags</SectionHeader>
      <SectionDescription>
        Small inline labels for status display and categorization. Four variants
        cover the full range of intent — success and error for state feedback,
        primary for new items, and secondary for edited ones. Add an{' '}
        <code className="text-p2 rounded bg-grey-150 px-1">onRemove</code> handler
        to show a dismiss button for user-removable selections.
      </SectionDescription>

      <p className="text-p3 mb-2 font-semibold tracking-wider text-grey-400 uppercase">
        Usage
      </p>
      <div className="space-y-6">
        <ComponentPreview title="Status Tags" code={TAG_STATUS_CODE}>
          <div className="flex flex-wrap gap-3">
            <Tag variant="success">DeliveriesData.xlsx</Tag>
            <Tag variant="success" onRemove={() => {}}>
              DeliveriesData.xlsx
            </Tag>
            <Tag variant="error">Missing Address</Tag>
          </div>
        </ComponentPreview>

        <ComponentPreview title="State Tags" code={TAG_STATE_CODE}>
          <div className="flex gap-3">
            <Tag variant="primary">New</Tag>
            <Tag variant="secondary">Edited</Tag>
          </div>
        </ComponentPreview>
      </div>
    </section>
  );
}
