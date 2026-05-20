import { Banner } from '@/common/components';

import { ComponentPreview } from '../components/ComponentPreview';
import { SectionDescription } from '../components/SectionDescription';
import { SectionHeader } from '../components/SectionHeader';
import { SectionLabel } from '../components/SectionLabel';

const BANNER_SUCCESS_CODE = `import { Banner } from '@/common/components';

<Banner
  variant="success"
  subtitle="Generated on Oct 20, 2025 at 10:42 AM"
>
  Routes generated successfully!
</Banner>`;

const BANNER_ERROR_CODE = `import { Banner } from '@/common/components';

<Banner variant="error">
  Unsupported format — please upload an Excel (.xlsx) file
</Banner>`;

const BANNER_WARNING_CODE = `import { Banner } from '@/common/components';

<Banner variant="warning">
  Warning — These entries will be skipped unless corrected.
</Banner>`;

export function BannersSection() {
  return (
    <section className="mb-16">
      <SectionHeader>Banners</SectionHeader>
      <SectionDescription>
        System-level alerts for user feedback and notifications. Three variants
        cover the full range of feedback scenarios: success, error, and warning.
        Banners support an optional{' '}
        <code className="text-p2 bg-grey-150 rounded px-1">subtitle</code> and a
        dismiss button via the{' '}
        <code className="text-p2 bg-grey-150 rounded px-1">onDismiss</code>{' '}
        prop.
      </SectionDescription>

      <SectionLabel>Usage</SectionLabel>
      <div className="space-y-6">
        <ComponentPreview
          title="Success"
          code={BANNER_SUCCESS_CODE}
          previewClassName="min-h-24 flex items-center justify-center p-6"
        >
          <div className="w-full max-w-2xl">
            <Banner
              variant="success"
              subtitle="Generated on Oct 20, 2025 at 10:42 AM"
            >
              Routes generated successfully!
            </Banner>
          </div>
        </ComponentPreview>

        <ComponentPreview
          title="Error"
          code={BANNER_ERROR_CODE}
          previewClassName="min-h-24 flex items-center justify-center p-6"
        >
          <div className="w-full max-w-2xl">
            <Banner variant="error">
              Unsupported format — please upload an Excel (.xlsx) file
            </Banner>
          </div>
        </ComponentPreview>

        <ComponentPreview
          title="Warning"
          code={BANNER_WARNING_CODE}
          previewClassName="min-h-24 flex items-center justify-center p-6"
        >
          <div className="w-full max-w-2xl">
            <Banner variant="warning">
              Warning — These entries will be skipped unless corrected.
            </Banner>
          </div>
        </ComponentPreview>
      </div>
    </section>
  );
}
