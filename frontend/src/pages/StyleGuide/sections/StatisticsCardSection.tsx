import { StatisticsCard } from '@/common/components';

import { ComponentPreview } from '../components/ComponentPreview';
import { SectionDescription } from '../components/SectionDescription';
import { SectionHeader } from '../components/SectionHeader';
import { SectionLabel } from '../components/SectionLabel';
import { SpecNote } from '../components/SpecNote';

const STATISTICS_CARD_CODE = `import { StatisticsCard } from '@/common/components';

<StatisticsCard
  color="green"
  label="Routes Created"
  value={3}
  character="granny"
/>`;

export function StatisticsCardSection() {
  return (
    <section className="mb-16">
      <SectionHeader>Statistics Card</SectionHeader>
      <SectionDescription>
        Displays a key metric with a label, value, illustrated character, and
        colored background. Used to summarize results at a glance, e.g. on the
        route generation success screen.
      </SectionDescription>

      <div className="mb-10 space-y-6">
        <SpecNote title="Color Variants">
          Four background colors: green (Brand Green), blue (Brand Light Blue),
          orange (Brand Orange), and pink (Brand Pink).
        </SpecNote>
        <SpecNote title="Character Variants">
          Five characters: boy, boyPointing, girlConfused, girlSearching, and
          granny. The character peeks up from the bottom-right edge of the card.
        </SpecNote>
        <SpecNote title="Sizing">
          Cards are full-width within their container. Use a flex/grid layout to
          place them side by side.
        </SpecNote>
      </div>

      <SectionLabel>Usage</SectionLabel>
      <div className="mb-8">
        <ComponentPreview title="Basic" code={STATISTICS_CARD_CODE}>
          <div className="w-80">
            <StatisticsCard
              color="green"
              label="Routes Created"
              value={3}
              character="granny"
            />
          </div>
        </ComponentPreview>
      </div>

      <SectionLabel>States</SectionLabel>
      <div className="border-grey-300 bg-grey-150 overflow-hidden rounded-xl border p-6">
        <div className="flex flex-col gap-8">
          <div>
            <p className="text-p3 mb-4 font-semibold tracking-wider text-blue-300 uppercase">
              Color Variants
            </p>
            <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
              <StatisticsCard
                color="green"
                label="Routes Created"
                value={3}
                character="granny"
              />
              <StatisticsCard
                color="blue"
                label="Total Families"
                value={515}
                character="boy"
              />
              <StatisticsCard
                color="pink"
                label="Average Stops"
                value={12}
                character="boyPointing"
              />
              <StatisticsCard
                color="orange"
                label="Longest Route"
                value="22 km"
                character="girlSearching"
              />
            </div>
          </div>

          <div>
            <p className="text-p3 mb-4 font-semibold tracking-wider text-blue-300 uppercase">
              Character Variants
            </p>
            <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
              <StatisticsCard
                color="green"
                label="Boy"
                value="—"
                character="boy"
              />
              <StatisticsCard
                color="green"
                label="Boy Pointing"
                value="—"
                character="boyPointing"
              />
              <StatisticsCard
                color="green"
                label="Girl Confused"
                value="—"
                character="girlConfused"
              />
              <StatisticsCard
                color="green"
                label="Girl Searching"
                value="—"
                character="girlSearching"
              />
              <StatisticsCard
                color="green"
                label="Granny"
                value="—"
                character="granny"
              />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
