import { Banner } from '@/common/components';

import { SectionHeader } from '../components/SectionHeader';

export function BannersSection() {
  return (
    <section className="mb-16">
      <SectionHeader>Banners</SectionHeader>

      <div className="space-y-6">
        <Banner
          variant="success"
          subtitle="Generated on Oct 20, 2025 at 10:42 AM"
        >
          Routes generated successfully!
        </Banner>

        <Banner variant="error">
          Unsupported format — please upload an Excel (.xlsx) file
        </Banner>

        <Banner variant="warning">
          Warning — These entries will be skipped unless corrected.
        </Banner>
      </div>
    </section>
  );
}
