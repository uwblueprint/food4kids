import { StatCard } from '@/common/components/StatCard';

import { SectionHeader } from '../components/SectionHeader';
import { SpecNote } from '../components/SpecNote';

export function StatCardSection() {
  return (
    <section className="mb-16">
      <SectionHeader>Stat Card</SectionHeader>

      <div className="mb-10 space-y-6">
        <SpecNote title="Usage">
          Displays a key metric with a label, value, illustrated character, and
          colored background. Used on the route generation success screen to
          summarize results at a glance.
        </SpecNote>

        <SpecNote title="Color Variants">
          Four background colors are available: green (Brand Green), blue (Brand
          Light Blue), orange (Brand Orange), and pink (Brand Pink).
        </SpecNote>

        <SpecNote title="Character Variants">
          Five characters can be placed on each card: boy, boyPointing,
          girlConfused, girlSearching, and granny. The character peeks up from
          the bottom-right edge of the card.
        </SpecNote>

        <SpecNote title="Sizing">
          Cards are full-width within their container. Use a flex/grid layout to
          place them side by side.
        </SpecNote>
      </div>

      <div className="border-grey-300 bg-grey-150 overflow-hidden rounded-xl border">
        <div className="flex flex-col gap-8 p-6">
          <div>
            <p className="text-p3 mb-4 font-semibold tracking-wider text-blue-300 uppercase">
              Color Variants
            </p>
            <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
              <StatCard color="green" label="Routes Created" value={3} character="granny" />
              <StatCard color="blue" label="Total Families" value={515} character="boy" />
              <StatCard color="pink" label="Average Stops" value={12} character="boyPointing" />
              <StatCard color="orange" label="Longest Route" value="22 km" character="girlSearching" />
            </div>
          </div>

          <div>
            <p className="text-p3 mb-4 font-semibold tracking-wider text-blue-300 uppercase">
              Character Variants (all on green)
            </p>
            <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
              <StatCard color="green" label="Boy" value="—" character="boy" />
              <StatCard color="green" label="Boy Pointing" value="—" character="boyPointing" />
              <StatCard color="green" label="Girl Confused" value="—" character="girlConfused" />
              <StatCard color="green" label="Girl Searching" value="—" character="girlSearching" />
              <StatCard color="green" label="Granny" value="—" character="granny" />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
