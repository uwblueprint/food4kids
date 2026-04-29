import { Spinner } from '@/common/components/Spinner';

import { ComponentPreview } from '../components/ComponentPreview';
import { SectionDescription } from '../components/SectionDescription';
import { SectionHeader } from '../components/SectionHeader';
import { SectionLabel } from '../components/SectionLabel';
import { SpecNote } from '../components/SpecNote';

const SPINNER_CODE = `import { Spinner } from '@/common/components';

<Spinner />`;

export function SpinnerSection() {
  return (
    <section className="mb-16">
      <SectionHeader>Spinner</SectionHeader>
      <SectionDescription>
        Loading indicator for in-progress operations. Renders a circular
        spinning border with a Blue/300 accent on a Grey/300 track. Three
        sizes are available via the{' '}
        <code className="text-p2 rounded bg-grey-150 px-1">size</code> prop.
      </SectionDescription>

      <div className="mb-10 space-y-6">
        <SpecNote title="Sizes">
          Three sizes: sm (32px), md (48px, default), and lg (64px). Border
          thickness scales with size for visual balance.
        </SpecNote>
      </div>

      <SectionLabel>Usage</SectionLabel>
      <div className="mb-8">
        <ComponentPreview title="Default" code={SPINNER_CODE}>
          <Spinner />
        </ComponentPreview>
      </div>

      <SectionLabel>States</SectionLabel>
      <div className="border-grey-300 bg-grey-150 overflow-hidden rounded-xl border">
        <div className="divide-grey-300 grid grid-cols-1 divide-y md:grid-cols-3 md:divide-x md:divide-y-0">
          <div className="flex flex-col items-start gap-4 p-6">
            <p className="text-p3 font-semibold tracking-wider text-blue-300 uppercase">
              Small
            </p>
            <Spinner size="sm" />
            <p className="text-p3 text-grey-400">size="sm" — 32px</p>
          </div>
          <div className="flex flex-col items-start gap-4 p-6">
            <p className="text-p3 font-semibold tracking-wider text-blue-300 uppercase">
              Medium (Default)
            </p>
            <Spinner size="md" />
            <p className="text-p3 text-grey-400">size="md" — 48px</p>
          </div>
          <div className="flex flex-col items-start gap-4 p-6">
            <p className="text-p3 font-semibold tracking-wider text-blue-300 uppercase">
              Large
            </p>
            <Spinner size="lg" />
            <p className="text-p3 text-grey-400">size="lg" — 64px</p>
          </div>
        </div>
      </div>
    </section>
  );
}
