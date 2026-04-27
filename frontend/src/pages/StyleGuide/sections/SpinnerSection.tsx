import { Spinner } from '@/common/components/Spinner';

import { SectionHeader } from '../components/SectionHeader';
import { SpecNote } from '../components/SpecNote';

export function SpinnerSection() {
  return (
    <section className="mb-16">
      <SectionHeader>Spinner</SectionHeader>

      <div className="mb-10 space-y-6">
        <SpecNote title="Usage">
          Used to indicate an in-progress operation. Renders a circular spinning
          border with a Blue/300 accent on a Grey/300 track.
        </SpecNote>

        <SpecNote title="Sizes">
          Three sizes are available: sm (32px), md (48px), and lg (64px). Border
          thickness scales with size for visual balance.
        </SpecNote>
      </div>

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
