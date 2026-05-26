import { SectionHeader } from '../components/SectionHeader';

export function SpacingSection() {
  return (
    <section className="mb-16">
      <SectionHeader>Spacing Scale (8px Grid)</SectionHeader>
      <p className="text-p2 text-grey-400 mb-6">
        Illustrates Tailwind&apos;s underlying doubling scale — not a list of
        approved design values. For the design&apos;s actual spacing increments
        (4, 8, 12, 16, 20, 24, 40, 80px) see the README spacing table.
      </p>

      <div className="space-y-3">
        {[
          { step: 0, px: 0, tw: '0' },
          { step: 1, px: 4, tw: '1' },
          { step: 2, px: 8, tw: '2' },
          { step: 3, px: 16, tw: '4' },
          { step: 4, px: 32, tw: '8' },
          { step: 5, px: 64, tw: '16' },
          { step: 6, px: 128, tw: '32' },
          { step: 7, px: 256, tw: '64' },
          { step: 8, px: 512, tw: '128' },
        ].map(({ step, px, tw }) => (
          <div key={step} className="flex items-center gap-4">
            <span className="text-p3 text-grey-400 w-6 text-right">{step}</span>
            <div
              className="bg-brand-pink h-2 rounded-sm"
              style={{ width: Math.min(px, 512) + 'px' }}
            />
            <span className="text-p3 text-grey-400">
              {px}px{' '}
              <code className="text-grey-500">
                p-{tw} / m-{tw}
              </code>
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}
