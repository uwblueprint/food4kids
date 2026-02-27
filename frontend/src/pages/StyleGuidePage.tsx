export const StyleGuidePage = () => {
  return (
    <div className="min-h-screen page-margins pb-16">
      <h1 className="mb-2 text-blue-300">
        F4K Design System
      </h1>
      <p className="text-p2 text-grey-400 mb-12">
        Tailwind CSS v4 theme — typography, colors, shadows, and spacing.
      </p>

      <hr className="border-grey-300 mb-12" />

      {/* ===== TYPEKIT ===== */}
      <section className="mb-16">
        <SectionHeader>Typekit</SectionHeader>

        <div className="border-grey-300 bg-grey-150 overflow-hidden rounded-xl border">
          <div className="divide-grey-300 grid grid-cols-1 divide-y md:grid-cols-3 md:divide-x md:divide-y-0">
            {/* Column 1: Typeface & Weights */}
            <div className="p-6">
              <p className="text-p3 mb-3 font-semibold tracking-wider text-blue-300 uppercase">
                Typeface & Weights
              </p>
              <p className="text-p3 text-grey-400 mb-6">
                Nunito is used for Heading text (except H3) and Button UI.
                Nunito Sans is used for Paragraph text.
              </p>
              <div className="space-y-3">
                <p className="font-nunito text-grey-500 text-xl font-extrabold">
                  Nunito ExtraBold
                </p>
                <p className="font-nunito text-grey-500 text-xl font-bold">
                  Nunito Bold
                </p>
                <p className="font-nunito text-grey-500 text-xl font-semibold">
                  Nunito SemiBold
                </p>
                <p className="font-nunito text-grey-500 text-xl font-medium">
                  Nunito Medium
                </p>
                <p className="font-nunito-sans text-grey-500 text-xl">
                  Nunito Sans Regular
                </p>
                <p className="font-nunito-sans text-grey-500 text-xl font-light">
                  Nunito Sans Light
                </p>
              </div>
            </div>

            {/* Column 2: Desktop & Tablet Text Styles */}
            <div className="p-6">
              <p className="text-p3 mb-3 font-semibold tracking-wider text-blue-300 uppercase">
                Desktop & Tablet Text Styles
              </p>
              <div className="space-y-5">
                <TypekitRow
                  label="Desktop/Heading/H1"
                  className="font-nunito text-h1 text-grey-500 font-bold"
                  spec="Nunito | Text size: 32px | Line height: 44px"
                  code="<h1>"
                />
                <TypekitRow
                  label="Desktop/Heading/H2"
                  className="font-nunito text-h2 text-grey-500 font-semibold"
                  spec="Nunito | Text size: 20px | Line height: 28px"
                  code="<h2>"
                />
                <TypekitRow
                  label="Desktop/Heading/H3"
                  className="font-nunito-sans text-h3 text-grey-500 font-bold"
                  spec="Nunito Sans | Text size: 16px | Line height: 20px"
                  code="<h3>"
                />
                <TypekitRow
                  label="Desktop/Paragraph/P1"
                  className="font-nunito-sans text-p1 text-grey-500"
                  spec="Nunito Sans | Text size: 16px | Line height: 20px"
                  code="text-p1"
                />
                <TypekitRow
                  label="Desktop/Paragraph/P2"
                  className="font-nunito-sans text-p2 text-grey-500"
                  spec="Nunito Sans | Text size: 14px | Line height: 18px"
                  code="text-p2"
                />
                <TypekitRow
                  label="Desktop/Paragraph/P3"
                  className="font-nunito-sans text-p3 text-grey-500"
                  spec="Nunito Sans | Text size: 12px | Line height: 18px"
                  code="text-p3"
                />
                <TypekitRow
                  label="UI/Button"
                  className="font-nunito text-h3 text-grey-500 font-bold"
                  spec="Nunito | Text size: 16px | Line height: 20px"
                  code="font-nunito font-bold"
                />
              </div>
            </div>

            {/* Column 3: Mobile Text Styles */}
            <div className="p-6">
              <p className="text-p3 mb-3 font-semibold tracking-wider text-blue-300 uppercase">
                Mobile Text Styles
              </p>
              <div className="space-y-5">
                <TypekitRow
                  label="Mobile/Heading/H1"
                  className="font-nunito text-m-h1 text-grey-500 font-bold"
                  spec="Nunito | Text size: 24px | Line height: 32px"
                  code="<h1>"
                />
                <TypekitRow
                  label="Mobile/Heading/H2"
                  className="font-nunito text-m-h2 text-grey-500 font-semibold"
                  spec="Nunito | Text size: 20px | Line height: 24px"
                  code="<h2>"
                />
                <TypekitRow
                  label="Mobile/Heading/H2/ExtraBold"
                  className="font-nunito text-m-h2 text-grey-500 font-extrabold"
                  spec="Nunito | Text size: 20px | Line height: 24px"
                  code="<h2> + font-extrabold"
                />
                <TypekitRow
                  label="Mobile/Heading/H3"
                  className="font-nunito-sans text-m-h3 text-grey-500 font-bold"
                  spec="Nunito Sans | Text size: 18px | Line height: 24px"
                  code="<h3>"
                />
                <TypekitRow
                  label="Mobile/Paragraph/P1"
                  className="font-nunito-sans text-m-p1 text-grey-500"
                  spec="Nunito Sans | Text size: 18px | Line height: 24px"
                  code="text-p1"
                />
                <TypekitRow
                  label="Mobile/Paragraph/P2"
                  className="font-nunito-sans text-m-p2 text-grey-500"
                  spec="Nunito Sans | Text size: 16px | Line height: 24px"
                  code="text-p2"
                />
                <TypekitRow
                  label="Mobile/Paragraph/P3"
                  className="font-nunito-sans text-m-p3 text-grey-500"
                  spec="Nunito Sans | Text size: 14px | Line height: 18px"
                  code="text-p3"
                />
                <TypekitRow
                  label="UI/Button"
                  className="font-nunito text-h3 text-grey-500 font-bold"
                  spec="Nunito | Text size: 16px | Line height: 20px"
                  code="font-nunito font-bold"
                />
              </div>
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

      {/* ===== SHADOWS ===== */}
      <section className="mb-16">
        <SectionHeader>Shadows</SectionHeader>

        <div className="flex gap-8">
          <div className="shadow-card flex h-32 w-64 items-center justify-center rounded-2xl bg-white">
            <div className="text-center">
              <p className="text-grey-500 font-semibold">shadow-card</p>
              <p className="text-p3 text-grey-400">
                0px 4px 10px rgba(0,0,0,0.05)
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ===== SPACING ===== */}
      <section className="mb-16">
        <SectionHeader>Spacing Scale (8px Grid)</SectionHeader>
        <p className="text-p2 text-grey-400 mb-6">
          Based on an 8px grid with 4px minor fallback. Maps to standard
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
              <span className="text-p3 text-grey-400 w-6 text-right">
                {step}
              </span>
              <div
                className="bg-brand-pink h-2 rounded-sm"
                style={{ width: Math.min(px, 512) }}
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

      {/* ===== BANNERS ===== */}
      <section className="mb-16">
        <SectionHeader>Banners (Token Usage Examples)</SectionHeader>

        <div className="space-y-6">
          <div className="border-success-stroke bg-success-fill flex items-start gap-2.5 rounded-2xl border px-4 py-6">
            <span className="text-success-stroke">&#10003;</span>
            <div>
              <p className="text-success-stroke font-semibold">
                Routes generated successfully!
              </p>
              <p className="text-p2 text-success-stroke opacity-80">
                Generated on Oct 20, 2025 at 10:42 AM
              </p>
            </div>
          </div>

          <div className="bg-light-red flex items-start gap-2.5 rounded-2xl border border-red px-4 py-6">
            <span className="text-red">&#9888;</span>
            <p className="text-p2 font-semibold text-red">
              Unsupported format — please upload an Excel (.xlsx) file
            </p>
          </div>

          <div className="border-dark-yellow bg-light-yellow flex items-start gap-2.5 rounded-2xl border px-4 py-6">
            <span className="text-dark-yellow">&#9888;</span>
            <p className="text-p2 text-dark-yellow font-semibold">
              Warning — These entries will be skipped unless corrected.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
};

/* ============================================== */
/* Helper Components                              */
/* ============================================== */

function SectionHeader({ children }: { children: React.ReactNode }) {
  return (
    <>
      <h2 className="mb-1">{children}</h2>
      <hr className="border-grey-300 mb-6" />
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
      <p className="text-p3 text-grey-500 font-semibold">
        {name}
      </p>
      <p className="text-p3 text-grey-400 font-mono">{hex}</p>
      <p className="text-p3 text-grey-400">{usage}</p>
    </div>
  );
}

function TypekitRow({
  label,
  className,
  spec,
  code,
}: {
  label: string;
  className: string;
  spec: string;
  code: string;
}) {
  return (
    <div>
      <p className={className}>{label}</p>
      <p className="text-p3 text-grey-400 mt-0.5">{spec}</p>
      <code className="bg-grey-200 text-p3 mt-1 inline-block rounded px-2 py-0.5 font-mono text-blue-300">
        {code}
      </code>
    </div>
  );
}
