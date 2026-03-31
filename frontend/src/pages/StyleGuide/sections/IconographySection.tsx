import { type ReactNode } from 'react';

import { SectionHeader } from '../components/SectionHeader';

export function IconographySection() {
  return (
    <section className="mb-16">
      <SectionHeader>Iconography</SectionHeader>

      <IconGroup title="Action">
        {[
          'clock',
          'more-vertical',
          'more-horizontal',
          'x',
          'phone',
          'megaphone',
          'search',
          'home',
          'map',
          'users',
          'settings',
          'printer',
          'edit',
          'mail',
          'trash',
          'plus',
          'minus',
          'expand-content',
          'collapse-content',
          'chevron-up',
          'chevron-down',
          'chevron-left',
          'chevron-right',
          'filter-lines',
          'copy',
          'share',
          'right-panel-close',
          'external-link',
          'undo',
        ].map((name) => (
          <IconTile key={name} name={name} />
        ))}
      </IconGroup>

      <IconGroup title="Metadata">
        {[
          'calendar',
          'map-pin',
          'box',
          'instagram',
          'facebook',
          'globe',
          'twitter',
          'heart',
          'award',
          'package',
        ].map((name) => (
          <IconTile key={`meta-${name}`} name={name} />
        ))}
      </IconGroup>

      <IconGroup title="Status">
        {[
          'check',
          'alert-circle',
          'alert-triangle',
          'wifi-off',
          'check-circle',
        ].map((name) => (
          <IconTile key={`status-${name}`} name={name} />
        ))}
      </IconGroup>
    </section>
  );
}

function IconGroup({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <div className="mb-8">
      <h3 className="text-p2 text-grey-500 mb-3 font-bold">{title}</h3>
      <div className="flex flex-wrap gap-4">{children}</div>
    </div>
  );
}

function IconTile({ name }: { name: string }) {
  return (
    <div className="border-grey-300 bg-grey-150 flex w-24 flex-col items-center gap-2 rounded-lg border px-2 py-3">
      <img
        src={new URL(`../../../assets/icons/${name}.svg`, import.meta.url).href}
        alt={name}
        className="size-6"
      />
      <p className="text-grey-400 text-center text-[10px] leading-tight">
        {name}
      </p>
    </div>
  );
}
