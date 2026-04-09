import { Tag } from '@/common/components';

import { SectionHeader } from '../components/SectionHeader';

export function TagsSection() {
  return (
    <section className="mb-16">
      <SectionHeader>Tags</SectionHeader>

      <div className="space-y-6">
        <div className="flex flex-wrap gap-3">
          <Tag variant="success">DeliveriesData.xlsx</Tag>
          <Tag variant="success" onRemove={() => {}}>
            DeliveriesData.xlsx
          </Tag>
          <Tag variant="error">Missing Address</Tag>
        </div>
      </div>
    </section>
  );
}
