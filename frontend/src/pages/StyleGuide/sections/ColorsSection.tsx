import { type ReactNode } from 'react';

import { SectionHeader } from '../components/SectionHeader';

export function ColorsSection() {
  return (
    <section className="mb-16">
      <SectionHeader>Colors</SectionHeader>

      <div className="space-y-10">
        <ColorGroup title="Primary Colours">
          <Swatch
            name="Grey/500"
            color="bg-grey-500"
            hex="#1C1B1F"
            usage="Global text color"
          />
          <Swatch
            name="Blue/300"
            color="bg-blue-300"
            hex="#226CA7"
            usage="Interactive elements"
          />
          <Swatch
            name="Grey/100"
            color="bg-grey-100 border border-grey-300"
            hex="#FFFFFF"
            usage="Global white color"
          />
        </ColorGroup>

        <ColorGroup title="Secondary Colours">
          <Swatch
            name="Blue/50"
            color="bg-blue-50"
            hex="#E9F4FF"
            usage="Hover states"
          />
          <Swatch
            name="Blue/400"
            color="bg-blue-400"
            hex="#195586"
            usage="Polylines"
          />
          <Swatch
            name="Grey/150"
            color="bg-grey-150"
            hex="#F8F8F8"
            usage="Form fields (uneditable)"
          />
          <Swatch
            name="Grey/200"
            color="bg-grey-200"
            hex="#EFF3F6"
            usage="Secondary buttons"
          />
          <Swatch
            name="Grey/300"
            color="bg-grey-300"
            hex="#E0E7ED"
            usage="Strokes"
          />
          <Swatch
            name="Grey/400"
            color="bg-grey-400"
            hex="#707581"
            usage="Metadata, archived data"
          />
        </ColorGroup>

        <ColorGroup title="Alerts">
          <Swatch
            name="Red"
            color="bg-red"
            hex="#EB3131"
            usage="Critical error stroke"
          />
          <Swatch
            name="Light Red"
            color="bg-light-red"
            hex="#FEF3F2"
            usage="Critical error fill"
          />
          <Swatch
            name="Dark Yellow"
            color="bg-dark-yellow"
            hex="#FDB022"
            usage="Warning stroke"
          />
          <Swatch
            name="Light Yellow"
            color="bg-light-yellow"
            hex="#FFFAEB"
            usage="Warning fill"
          />
          <Swatch
            name="Success/Stroke"
            color="bg-success-stroke"
            hex="#039855"
            usage="Success stroke"
          />
          <Swatch
            name="Success/Fill"
            color="bg-success-fill"
            hex="#ECFDF3"
            usage="Success fill"
          />
        </ColorGroup>

        <ColorGroup title="Supporting Colours">
          <Swatch
            name="Brand/Green"
            color="bg-brand-green"
            hex="#27B28D"
            usage="Cards, graphs"
          />
          <Swatch
            name="Brand/Light Blue"
            color="bg-brand-light-blue"
            hex="#09A7DF"
            usage="Cards, graphs"
          />
          <Swatch
            name="Brand/Orange"
            color="bg-brand-orange"
            hex="#EB5531"
            usage="Cards, graphs"
          />
          <Swatch
            name="Brand/Pink"
            color="bg-brand-pink"
            hex="#B33F93"
            usage="Cards, graphs"
          />
        </ColorGroup>
      </div>
    </section>
  );
}

function ColorGroup({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <div>
      <p className="text-p2 text-grey-500 mb-3 font-bold">{title}</p>
      <div className="flex flex-wrap gap-4">{children}</div>
    </div>
  );
}

function Swatch({
  name,
  color,
  hex,
  usage,
}: {
  name: string;
  color: string;
  hex: string;
  usage: string;
}) {
  return (
    <div className="w-36">
      <div className={`mb-2 h-16 rounded-md ${color}`} />
      <p className="text-p3 text-grey-500 font-semibold">{name}</p>
      <p className="text-p3 text-grey-400 font-mono">{hex}</p>
      <p className="text-p3 text-grey-400">{usage}</p>
    </div>
  );
}
