export const StyleGuidePage = () => {
  return (
    <div className="font-nunito-sans text-dark min-h-screen bg-white p-8 md:p-16">
      <h1 className="font-nunito mb-2 text-[2.5rem] leading-tight font-bold text-blue-300">
        F4K Design System
      </h1>
      <p className="text-p1 text-light mb-12">
        Tailwind CSS v4 theme tokens — fonts, colors, shadows, and spacing.
      </p>

      <hr className="mb-12 border-gray-300" />

      {/* ===== FONTS ===== */}
      <section className="mb-16">
        <SectionHeader>Fonts</SectionHeader>

        <div className="flex flex-wrap gap-12">
          <div>
            <p className="text-p3 text-grey-400 mb-2 font-semibold tracking-wider uppercase">
              Nunito
            </p>
            <p className="font-nunito text-[2.5rem] font-bold">Nunito Bold</p>
            <p className="font-nunito text-[2.5rem] font-semibold">
              Nunito SemiBold
            </p>
            <p className="font-nunito text-[2.5rem]">Nunito Regular</p>
          </div>
          <div>
            <p className="text-p3 text-grey-400 mb-2 font-semibold tracking-wider uppercase">
              Nunito Sans
            </p>
            <p className="font-nunito-sans text-[2.5rem] font-bold">
              Nunito Sans Bold
            </p>
            <p className="font-nunito-sans text-[2.5rem]">
              Nunito Sans Regular
            </p>
          </div>
        </div>
      </section>

      {/* ===== TYPEKIT ===== */}
      <section className="mb-16">
        <SectionHeader>Typekit</SectionHeader>

        <div className="grid grid-cols-1 gap-10 md:grid-cols-3">
          {/* --- Typeface & Weights --- */}
          <div>
            <p className="text-p3 mb-4 font-semibold tracking-wider text-blue-300 uppercase">
              Typeface &amp; Weights
            </p>
            <p className="text-p2 text-grey-400 mb-6">
              Nunito is used for Heading text (except H3) and Button UI. Nunito
              Sans is used for Paragraph text.
            </p>
            <div className="space-y-2">
              <p className="font-nunito text-xl font-extrabold">
                Nunito ExtraBold
              </p>
              <p className="font-nunito text-xl font-bold">Nunito Bold</p>
              <p className="font-nunito text-xl font-semibold">
                Nunito SemiBold
              </p>
              <p className="font-nunito text-xl font-medium">Nunito Medium</p>
              <p className="font-nunito-sans text-xl">Nunito Sans Regular</p>
              <p className="font-nunito-sans text-xl font-light">
                Nunito Sans Light
              </p>
            </div>
          </div>

          {/* --- Desktop & Tablet Text Styles --- */}
          <div>
            <p className="text-p3 mb-4 font-semibold tracking-wider text-blue-300 uppercase">
              Desktop &amp; Tablet Text Styles
            </p>
            <div className="space-y-5">
              <TypeEntry
                as="h1"
                spec="Nunito | Text size: 32px | Line height: 44px"
              />
              <TypeEntry
                as="h2"
                spec="Nunito | Text size: 20px | Line height: 28px"
              />
              <TypeEntry
                as="h3"
                spec="Nunito Sans | Text size: 16px | Line height: 20px"
              />
              <TypeEntry
                label="Desktop/Paragraph/P1"
                className="font-nunito-sans text-p1"
                spec="Nunito Sans | Text size: 16px | Line height: 20px"
              />
              <TypeEntry
                label="Desktop/Paragraph/P2"
                className="font-nunito-sans text-p2"
                spec="Nunito Sans | Text size: 14px | Line height: 18px"
              />
              <TypeEntry
                label="UI/Button"
                className="font-nunito text-h3 font-normal"
                spec="Nunito | Text size: 16px | Line height: 20px"
              />
            </div>
          </div>

          {/* --- Mobile Text Styles --- */}
          <div>
            <p className="text-p3 mb-4 font-semibold tracking-wider text-blue-300 uppercase">
              Mobile Text Styles
            </p>
            <div className="space-y-5">
              <TypeEntry
                label="Mobile/Heading/H1"
                className="font-nunito text-m-h1 font-normal"
                spec="Nunito | Text size: 24px | Line height: 32px"
              />
              <TypeEntry
                label="Mobile/Heading/H2"
                className="font-nunito text-m-h2 font-normal"
                spec="Nunito | Text size: 20px | Line height: 24px"
              />
              <TypeEntry
                label="Mobile/Heading/H2/ExtraBold"
                className="font-nunito text-m-h2 font-extrabold"
                spec="Nunito | Text size: 20px | Line height: 24px"
              />
              <TypeEntry
                label="Mobile/Heading/H3"
                className="font-nunito-sans text-m-h3 font-bold"
                spec="Nunito Sans | Text size: 18px | Line height: 24px"
              />
              <TypeEntry
                label="Mobile/Paragraph/P1"
                className="font-nunito-sans text-m-p1"
                spec="Nunito Sans | Text size: 18px | Line height: 24px"
              />
              <TypeEntry
                label="Mobile/Paragraph/P2"
                className="font-nunito-sans text-m-p2"
                spec="Nunito Sans | Text size: 16px | Line height: 24px"
              />
              <TypeEntry
                label="Mobile/Paragraph/P3"
                className="font-nunito-sans text-m-p3"
                spec="Nunito Sans | Text size: 14px | Line height: 18px"
              />
              <TypeEntry
                label="UI/Button"
                className="font-nunito text-h3 font-normal"
                spec="Nunito | Text size: 16px | Line height: 20px"
              />
            </div>
          </div>
        </div>
      </section>

      {/* ===== COLORS ===== */}
      <section className="mb-16">
        <SectionHeader>Colors</SectionHeader>

        <div className="space-y-10">
          <ColorGroup title="Primary Colours">
            <Swatch
              name="Grey/500"
              color="bg-grey-500"
              hex="#1C1B1F"
              usage="Global text color"
              light
            />
            <Swatch
              name="Blue/300"
              color="bg-blue-300"
              hex="#226CA7"
              usage="Interactive elements"
              light
            />
            <Swatch
              name="Grey/100"
              color="bg-grey-100 border border-gray-200"
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
              light
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
              light
            />
          </ColorGroup>

          <ColorGroup title="Alerts">
            <Swatch
              name="Red"
              color="bg-[var(--color-red)]"
              hex="#EB3131"
              usage="Critical error banner stroke"
              light
            />
            <Swatch
              name="Light Red"
              color="bg-light-red"
              hex="#FEF3F2"
              usage="Critical error banner fill"
            />
            <Swatch
              name="Dark Yellow"
              color="bg-dark-yellow"
              hex="#FDB022"
              usage="Warning text or banner stroke"
            />
            <Swatch
              name="Light Yellow"
              color="bg-light-yellow"
              hex="#FFFAEB"
              usage="Warning banner fill"
            />
            <Swatch
              name="Success/Stroke"
              color="bg-success-stroke"
              hex="#039855"
              usage="Successful text or banner stroke"
              light
            />
            <Swatch
              name="Success/Fill"
              color="bg-success-fill"
              hex="#ECFDF3"
              usage="Successful banner fill"
            />
          </ColorGroup>

          <ColorGroup title="Supporting Colours">
            <Swatch
              name="Brand/Green"
              color="bg-brand-green"
              hex="#27B28D"
              usage="Card Background, Statistics Graph"
              light
            />
            <Swatch
              name="Brand/Light Blue"
              color="bg-brand-light-blue"
              hex="#09A7DF"
              usage="Card Background, Statistics Graph"
              light
            />
            <Swatch
              name="Brand/Orange"
              color="bg-brand-orange"
              hex="#EB5531"
              usage="Card Background, Statistics Graph"
              light
            />
            <Swatch
              name="Brand/Pink"
              color="bg-brand-pink"
              hex="#B33F93"
              usage="Card Background, Statistics Graph"
              light
            />
          </ColorGroup>
        </div>
      </section>

      {/* ===== SHADOWS ===== */}
      <section className="mb-16">
        <SectionHeader>Shadows</SectionHeader>

        <div className="flex gap-8">
          <div className="shadow-card flex h-32 w-64 items-center justify-center rounded-2xl bg-white">
            <div className="text-center">
              <p className="text-dark font-semibold">shadow-card</p>
              <p className="text-p3 text-light">
                0px 4px 10px rgba(0,0,0,0.05)
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ===== SPACING ===== */}
      <section className="mb-16">
        <SectionHeader>Spacing Scale (8px Grid)</SectionHeader>
        <p className="text-p2 text-light mb-6">
          Based on an 8px grid with 4px minor grid fallback. Maps to standard
          Tailwind utilities.
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
              <span className="text-p3 text-light w-6 text-right">{step}</span>
              <div
                className="bg-brand-pink h-2 rounded-sm"
                style={{ width: Math.min(px, 512) }}
              />
              <span className="text-p3 text-light">
                {px}px{' '}
                <code className="text-dark">
                  p-{tw} / m-{tw}
                </code>
              </span>
            </div>
          ))}
        </div>
      </section>

      {/* ===== BANNER EXAMPLES ===== */}
      <section className="mb-16">
        <SectionHeader>Banners (Token Usage Examples)</SectionHeader>

        <div className="space-y-6">
          <div className="border-success-800 bg-success-fill flex items-start gap-2.5 rounded-2xl border px-4 py-6">
            <span className="text-success-stroke">&#10003;</span>
            <div>
              <p className="text-success-stroke font-semibold">
                Routes generated successfully!
              </p>
              <p className="text-p2 text-success-900">
                Generated on Oct 20, 2025 at 10:42 AM
              </p>
            </div>
          </div>

          <div className="border-error-stroke bg-error-fill flex items-start gap-2.5 rounded-2xl border px-4 py-6">
            <span className="text-error-stroke">&#9888;</span>
            <p className="text-p2 text-error-stroke font-semibold">
              Unsupported format — please upload an Excel (.xlsx) file
            </p>
          </div>

          <div className="border-warning-400 bg-warning-50 flex items-start gap-2.5 rounded-2xl border px-4 py-6">
            <span className="text-warning-900">&#9888;</span>
            <p className="text-p2 text-warning-900 font-semibold">
              Warning — These entries will be skipped unless corrected.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
};

/* --- Helper Components --- */

function SectionHeader({ children }: { children: React.ReactNode }) {
  return (
    <>
      <h2 className="font-nunito text-h2 text-dark mb-1 font-semibold">
        {children}
      </h2>
      <hr className="mb-6 border-gray-300" />
    </>
  );
}

function ColorGroup({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <h3 className="text-p2 text-dark mb-3 font-bold">{title}</h3>
      <div className="flex flex-wrap gap-4">{children}</div>
    </div>
  );
}

function Swatch({
  name,
  color,
  hex,
  usage,
  light = false,
}: {
  name: string;
  color: string;
  hex: string;
  usage: string;
  light?: boolean;
}) {
  return (
    <div className="w-36">
      <div className={`mb-2 h-16 rounded-md ${color}`} />
      <p className={`text-p3 font-semibold ${light ? '' : 'text-dark'}`}>
        {name}
      </p>
      <p className="text-p3 text-light font-mono">{hex}</p>
      <p className="text-p3 text-light">{usage}</p>
    </div>
  );
}

function TypeEntry({
  as: Component,
  label,
  className,
  spec,
}: {
  as?: 'h1' | 'h2' | 'h3';
  label?: string;
  className?: string;
  spec: string;
}) {
  const defaultLabels = {
    h1: 'Desktop/Heading/H1',
    h2: 'Desktop/Heading/H2',
    h3: 'Desktop/Heading/H3',
  };
  const displayLabel = label ?? (Component ? defaultLabels[Component] : '');

  return (
    <div>
      {Component ? (
        <Component>{displayLabel}</Component>
      ) : (
        <p className={className}>{displayLabel}</p>
      )}
      <p className="text-p3 text-grey-400">{spec}</p>
    </div>
  );
}
