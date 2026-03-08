import type { ReactNode } from 'react';

import { Button } from '@/common/components/Button';

export const StyleGuidePage = () => {
  return (
    <div className="page-margins min-h-screen pb-16">
      <h1 className="mb-2 text-blue-300">F4K Design System</h1>
      <p className="text-p2 text-grey-400 mb-2">
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
            {/* NOTE: text-m-* tokens are used here intentionally to display
                static mobile sizes for documentation purposes. They must NOT
                be used directly in any other component — use text-p1/p2/p3
                or h1/h2/h3 (which apply mobile sizes automatically via
                @layer base/@layer utilities). */}
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
          Illustrates Tailwind&apos;s underlying doubling scale — not a list of
          approved design values. For the design&apos;s actual spacing
          increments (4, 8, 12, 16, 20, 24, 40, 80px) see the README spacing
          table.
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

          <div className="bg-light-red border-red flex items-start gap-2.5 rounded-2xl border px-4 py-6">
            <span className="text-red">&#9888;</span>
            <p className="text-p2 text-red font-semibold">
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

      {/* ===== ILLUSTRATIONS ===== */}
      <section className="mb-16">
        <SectionHeader>Illustrations</SectionHeader>
        <div className="flex flex-wrap gap-6">
          {[
            { file: 'boy.png', label: 'boy' },
            {
              file: 'boy-edge-case-no-question-mark.png',
              label: 'boy-edge-case-no-question-mark',
            },
            {
              file: 'boy-edge-case-with-questions.png',
              label: 'boy-edge-case-with-questions',
            },
            { file: 'girl-403.png', label: 'girl-403' },
            { file: 'girl-confused.png', label: 'girl-confused' },
            { file: 'granny.png', label: 'granny' },
          ].map(({ file, label }) => (
            <div
              key={file}
              className="border-grey-300 bg-grey-150 flex flex-col items-center gap-2 rounded-lg border p-4"
            >
              <img
                src={`/illustrations/${file}`}
                alt={label}
                className="h-32 w-auto object-contain"
              />
              <p className="text-grey-400 text-center text-[10px] leading-tight">
                {label}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* ===== LOGOS ===== */}
      <section className="mb-16">
        <SectionHeader>Logos</SectionHeader>
        <div className="flex flex-wrap gap-6">
          {[
            {
              file: 'logo_desktop_two_lines.png',
              label: 'logo_desktop_two_lines',
            },
            { file: 'logo_mobile_one_line.png', label: 'logo_mobile_one_line' },
          ].map(({ file, label }) => (
            <div
              key={file}
              className="border-grey-300 bg-grey-150 flex flex-col items-center gap-2 rounded-lg border p-4"
            >
              <img
                src={`/logos/${file}`}
                alt={label}
                className="h-16 w-auto object-contain"
              />
              <p className="text-grey-400 text-center text-[10px] leading-tight">
                {label}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* ===== ICONOGRAPHY ===== */}
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

      <section className="mb-16">
        {/* Section header (matches existing StyleGuide pattern) */}
        <h2 className="mb-1">Call to Action Buttons</h2>
        <hr className="border-grey-300 mb-6" />

        {/* ---- Spec notes ---- */}
        <div className="mb-10 space-y-6">
          <SpecNote title="Button Height">
            Button height is 44px across desktop, tablet, and mobile.
          </SpecNote>

          <SpecNote title="Button Width">
            Width is auto based on container size, with 24px horizontal padding
            (left and right).
            <br />
            <br />
            Minimum width is 104px.
          </SpecNote>

          <SpecNote title="Mobile Button">
            On mobile, buttons span the full width of their container.
          </SpecNote>

          <SpecNote title="Border Radius">
            Border radius defaults to 40px on all corners.
          </SpecNote>

          <SpecNote title="Circular Button">
            Circular icon buttons are 44px × 44px.
          </SpecNote>
        </div>

        {/* ---- Rectangular button grid ---- */}
        <div className="border-grey-300 bg-grey-150 overflow-hidden rounded-xl border">
          <div className="divide-grey-300 grid grid-cols-2 divide-y md:grid-cols-4 md:divide-x md:divide-y-0">
            {/* Primary */}
            <ButtonColumn title="Primary">
              <ButtonDemo label="Default State">
                <Button variant="primary">Save</Button>
              </ButtonDemo>
              <ButtonDemo label="Hover State">
                <Button variant="primary" className="!bg-blue-400">
                  Save
                </Button>
              </ButtonDemo>
            </ButtonColumn>

            {/* Secondary */}
            <ButtonColumn title="Secondary">
              <ButtonDemo label="Default State">
                <Button variant="secondary">Cancel</Button>
              </ButtonDemo>
              <ButtonDemo label="Hover State">
                <Button variant="secondary" className="!bg-grey-300">
                  Cancel
                </Button>
              </ButtonDemo>
            </ButtonColumn>

            {/* Tertiary */}
            <ButtonColumn title="Tertiary">
              <ButtonDemo label="Default State">
                <Button variant="tertiary">Cancel</Button>
              </ButtonDemo>
              <ButtonDemo label="Hover State">
                <Button variant="tertiary">Cancel</Button>
              </ButtonDemo>
            </ButtonColumn>

            {/* Text Link */}
            <ButtonColumn title="Text Link">
              <ButtonDemo label="Default State">
                <Button variant="textLink">Text</Button>
              </ButtonDemo>
              <ButtonDemo label="Hover State">
                <Button variant="textLink" className="underline">
                  Text
                </Button>
              </ButtonDemo>
            </ButtonColumn>
          </div>
        </div>

        {/* ---- Circular buttons ---- */}
        <h3 className="mt-10 mb-1">Circular Buttons</h3>
        <hr className="border-grey-300 mb-6" />

        <div className="border-grey-300 bg-grey-150 overflow-hidden rounded-xl border">
          <div className="divide-grey-300 grid grid-cols-3 divide-x">
            {/* Circular Primary */}
            <ButtonColumn title="Circular Primary">
              <ButtonDemo label="Default State">
                <Button variant="primary" shape="circular" aria-label="Next">
                  <ChevronRightIcon />
                </Button>
              </ButtonDemo>
              <ButtonDemo label="Hover State">
                <Button
                  variant="primary"
                  shape="circular"
                  className="!bg-blue-400"
                  aria-label="Next"
                >
                  <ChevronRightIcon />
                </Button>
              </ButtonDemo>
            </ButtonColumn>

            {/* Circular Secondary */}
            <ButtonColumn title="Circular Secondary">
              <ButtonDemo label="Default State">
                <Button variant="secondary" shape="circular" aria-label="Next">
                  <ChevronRightIcon className="text-grey-500" />
                </Button>
              </ButtonDemo>
              <ButtonDemo label="Hover State">
                <Button
                  variant="secondary"
                  shape="circular"
                  className="!bg-grey-300"
                  aria-label="Next"
                >
                  <ChevronRightIcon className="text-grey-500" />
                </Button>
              </ButtonDemo>
            </ButtonColumn>

            {/* Circular Tertiary */}
            <ButtonColumn title="Circular Tertiary">
              <ButtonDemo label="Default State">
                <Button variant="tertiary" shape="circular" aria-label="Next">
                  <ChevronRightIcon className="text-grey-500" />
                </Button>
              </ButtonDemo>
              <ButtonDemo label="Hover State">
                <Button variant="tertiary" shape="circular" aria-label="Next">
                  <ChevronRightIcon className="text-grey-500" />
                </Button>
              </ButtonDemo>
            </ButtonColumn>
          </div>
        </div>
      </section>
    </div>
  );
};

/* ============================================== */
/* Helper Components                              */
/* ============================================== */

function SpecNote({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <p className="text-p3 mb-1 font-semibold tracking-wider text-blue-300 uppercase">
        {title}
      </p>
      <p className="text-p1 text-grey-500">{children}</p>
    </div>
  );
}

function ButtonColumn({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="p-6">
      <p className="text-p3 mb-4 font-semibold tracking-wider text-blue-300 uppercase">
        {title}
      </p>
      <div className="space-y-6">{children}</div>
    </div>
  );
}

function ButtonDemo({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-start gap-2">
      {children}
      <p className="text-p3 text-grey-400">{label}</p>
    </div>
  );
}

/** Inline chevron-right SVG matching the icon set at /icons/chevron-right.svg */
function ChevronRightIcon({ className = '' }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <polyline points="9 18 15 12 9 6" />
    </svg>
  );
}

function SectionHeader({ children }: { children: ReactNode }) {
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
      <img src={`/icons/${name}.svg`} alt={name} className="size-6" />
      <p className="text-grey-400 text-center text-[10px] leading-tight">
        {name}
      </p>
    </div>
  );
}
