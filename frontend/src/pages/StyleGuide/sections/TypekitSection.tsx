import { SectionHeader } from '../components/SectionHeader';

export function TypekitSection() {
  return (
    <section className="mb-16">
      <SectionHeader>Typekit</SectionHeader>

      <div className="border-grey-300 bg-grey-150 overflow-hidden rounded-xl border">
        <div className="divide-grey-300 grid grid-cols-1 divide-y md:grid-cols-3 md:divide-x md:divide-y-0">
          {/* Column 1: Typeface & Weights */}
          <div className="min-w-0 p-6">
            <p className="text-p3 mb-3 font-semibold tracking-wider text-blue-300 uppercase">
              Typeface & Weights
            </p>
            <p className="text-p3 text-grey-400 mb-6">
              Nunito is used for Heading text (except H3) and Button UI. Nunito
              Sans is used for Paragraph text.
            </p>
            <div className="space-y-3">
              <p className="text-grey-500 text-xl font-extrabold">
                Nunito ExtraBold
              </p>
              <p className="text-grey-500 text-xl font-bold">Nunito Bold</p>
              <p className="text-grey-500 text-xl font-semibold">
                Nunito SemiBold
              </p>
              <p className="text-grey-500 text-xl font-medium">Nunito Medium</p>
              <p className="text-grey-500 text-xl">Nunito Sans Regular</p>
              <p className="text-grey-500 text-xl font-light">
                Nunito Sans Light
              </p>
            </div>
          </div>

          {/* Column 2: Desktop & Tablet Text Styles */}
          <div className="min-w-0 p-6">
            <p className="text-p3 mb-3 font-semibold tracking-wider text-blue-300 uppercase">
              Desktop & Tablet Text Styles
            </p>
            <div className="space-y-5">
              <TypekitRow
                as="h1"
                label="Desktop/Heading/H1"
                className="text-h1 text-grey-500 font-bold"
                spec="Nunito | Text size: 32px | Line height: 44px"
                code="<h1>"
              />
              <TypekitRow
                as="h2"
                label="Desktop/Heading/H2"
                className="text-h2 text-grey-500 font-semibold"
                spec="Nunito | Text size: 20px | Line height: 28px"
                code="<h2>"
              />
              <TypekitRow
                as="h3"
                label="Desktop/Heading/H3"
                className="text-h3 text-grey-500 font-bold"
                spec="Nunito Sans | Text size: 16px | Line height: 20px"
                code="<h3>"
              />
              <TypekitRow
                label="Desktop/Paragraph/P1"
                className="text-grey-500 text-[var(--text-p1)]"
                spec="Nunito Sans | Text size: 16px | Line height: 20px"
                code="text-p1"
              />
              <TypekitRow
                label="Desktop/Paragraph/P2"
                className="text-grey-500 text-[var(--text-p2)]"
                spec="Nunito Sans | Text size: 14px | Line height: 18px"
                code="text-p2"
              />
              <TypekitRow
                label="Desktop/Paragraph/P3"
                className="text-grey-500 text-[var(--text-p3)]"
                spec="Nunito Sans | Text size: 12px | Line height: 18px"
                code="text-p3"
              />
              <TypekitRow
                label="UI/Button"
                className="text-h3 text-grey-500 font-bold"
                spec="Nunito | Text size: 16px | Line height: 20px"
                code="font-nunito font-bold"
              />
            </div>
          </div>

          {/* Column 3: Mobile Text Styles */}
          {/* NOTE: text-m-* tokens are used here intentionally to display
              static mobile sizes for documentation purposes. They must NOT
              be used directly in any other component — use text-p1/p2/p3
              or h1/h2/h3 (which apply mobile sizes automatically via
              @layer base/@layer utilities). */}
          <div className="min-w-0 p-6">
            <p className="text-p3 mb-3 font-semibold tracking-wider text-blue-300 uppercase">
              Mobile Text Styles
            </p>
            <div className="space-y-5">
              <TypekitRow
                as="h1"
                label="Mobile/Heading/H1"
                className="text-m-h1 text-grey-500 font-bold"
                spec="Nunito | Text size: 24px | Line height: 32px"
                code="<h1>"
              />
              <TypekitRow
                as="h2"
                label="Mobile/Heading/H2"
                className="text-m-h2 text-grey-500 font-semibold"
                spec="Nunito | Text size: 20px | Line height: 24px"
                code="<h2>"
              />
              <TypekitRow
                as="h2"
                label="Mobile/Heading/H2/ExtraBold"
                className="text-m-h2 text-grey-500"
                classNameAddons="font-extrabold"
                spec="Nunito | Text size: 20px | Line height: 24px"
                code="<h2> + font-extrabold"
              />
              <TypekitRow
                as="h3"
                label="Mobile/Heading/H3"
                className="text-m-h3 text-grey-500 font-bold"
                spec="Nunito Sans | Text size: 18px | Line height: 24px"
                code="<h3>"
              />
              <TypekitRow
                label="Mobile/Paragraph/P1"
                className="text-m-p1 text-grey-500"
                spec="Nunito Sans | Text size: 18px | Line height: 24px"
                code="text-p1"
              />
              <TypekitRow
                label="Mobile/Paragraph/P2"
                className="text-m-p2 text-grey-500"
                spec="Nunito Sans | Text size: 16px | Line height: 24px"
                code="text-p2"
              />
              <TypekitRow
                label="Mobile/Paragraph/P3"
                className="text-m-p3 text-grey-500"
                spec="Nunito Sans | Text size: 14px | Line height: 18px"
                code="text-p3"
              />
              <TypekitRow
                label="UI/Button"
                className="text-h3 text-grey-500 font-bold"
                spec="Nunito | Text size: 16px | Line height: 20px"
                code="font-nunito font-bold"
              />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function TypekitRow({
  label,
  as: Tag = 'p',
  className,
  classNameAddons,
  spec,
  code,
}: {
  label: string;
  as?: 'h1' | 'h2' | 'h3' | 'p';
  className: string;
  classNameAddons?: string;
  spec: string;
  code: string;
}) {
  return (
    <div className="overflow-hidden">
      {/* FYI, these use className and overides to ensure consistent behavior for both mobile and desktop */}
      <Tag
        className={`${className}${classNameAddons ? ` ${classNameAddons}` : ''} truncate`}
      >
        {label}
      </Tag>
      <p className="text-p3 text-grey-400 mt-0.5">{spec}</p>
      <code className="bg-grey-200 text-p3 mt-1 inline-block rounded px-2 py-0.5 font-mono break-all text-blue-300">
        {code}
      </code>
    </div>
  );
}
