export const StyleGuidePage = () => {
  return (
    <div className="min-h-screen bg-white p-8 font-nunito-sans text-dark md:p-16">
      <h1 className="mb-2 font-nunito text-[2.5rem] font-bold leading-tight text-blue-300">
        F4K Design System
      </h1>
      <p className="mb-12 text-p1 text-light">
        Tailwind CSS v4 theme tokens — fonts, colors, shadows, and spacing.
      </p>

      <hr className="mb-12 border-gray-300" />

      {/* ===== FONTS ===== */}
      <section className="mb-16">
        <SectionHeader>Fonts</SectionHeader>

        <div className="flex flex-wrap gap-12">
          <div>
            <p className="mb-2 text-p3 font-semibold uppercase tracking-wider text-grey-400">
              Nunito
            </p>
            <p className="font-nunito text-[2.5rem] font-bold">Nunito Bold</p>
            <p className="font-nunito text-[2.5rem] font-semibold">
              Nunito SemiBold
            </p>
            <p className="font-nunito text-[2.5rem]">Nunito Regular</p>
          </div>
          <div>
            <p className="mb-2 text-p3 font-semibold uppercase tracking-wider text-grey-400">
              Nunito Sans
            </p>
            <p className="font-nunito-sans text-[2.5rem] font-bold">
              Nunito Sans Bold
            </p>
            <p className="font-nunito-sans text-[2.5rem]">
              Nunito Sans Regular
            </p>
          </div>
          <div>
            <p className="mb-2 text-p3 font-semibold uppercase tracking-wider text-grey-400">
              Titillium Web
            </p>
            <p className="font-titillium text-[2.5rem] font-semibold">
              Titillium Web SemiBold
            </p>
            <p className="font-titillium text-[2.5rem]">
              Titillium Web Regular
            </p>
          </div>
        </div>
      </section>

      {/* ===== TYPOGRAPHY: DESKTOP ===== */}
      <section className="mb-16">
        <SectionHeader>Typography — Desktop / Tablet</SectionHeader>
        <p className="mb-6 text-p2 text-light">
          Uses <code className="text-blue-300">font-titillium</code>
        </p>

        <div className="space-y-4">
          <TypeRow
            label="H1 — Page Header"
            spec="32px / 40px · SemiBold"
            className="font-titillium text-h1 font-semibold"
          />
          <TypeRow
            label="H2 — Subheader"
            spec="24px / 32px · SemiBold"
            className="font-titillium text-h2 font-semibold"
          />
          <TypeRow
            label="H3 — Labels, Links & Buttons"
            spec="14px / 22px · SemiBold"
            className="font-titillium text-h3 font-semibold"
          />
          <TypeRow
            label="H4 — Table Header"
            spec="12px / 18px · SemiBold · Uppercase"
            className="font-titillium text-h4 font-semibold uppercase"
          />
          <TypeRow
            label="P1 — Body Large"
            spec="16px / 28px · Regular"
            className="font-titillium text-p1"
          />
          <TypeRow
            label="P2 — Body Medium"
            spec="14px / 22px · Regular"
            className="font-titillium text-p2"
          />
          <TypeRow
            label="P3 — Body Small"
            spec="12px / 18px · Regular"
            className="font-titillium text-p3"
          />
        </div>
      </section>

      {/* ===== TYPOGRAPHY: MOBILE ===== */}
      <section className="mb-16">
        <SectionHeader>Typography — Mobile</SectionHeader>
        <p className="mb-6 text-p2 text-light">
          Headings use <code className="text-blue-300">font-nunito</code>, body
          uses <code className="text-blue-300">font-nunito-sans</code>
        </p>

        <div className="space-y-4">
          <TypeRow
            label="M H1 — Page Header"
            spec="24px / 32px · Bold · Nunito"
            className="font-nunito text-m-h1 font-bold"
          />
          <TypeRow
            label="M H2 — Subheader"
            spec="20px / 24px · SemiBold · Nunito"
            className="font-nunito text-m-h2 font-semibold"
          />
          <TypeRow
            label="M H3 — Labels, Links & Buttons"
            spec="18px / 24px · Bold · Nunito Sans"
            className="font-nunito-sans text-m-h3 font-bold"
          />
          <TypeRow
            label="M P1 — Body Large"
            spec="18px / 24px · Regular · Nunito Sans"
            className="font-nunito-sans text-m-p1"
          />
          <TypeRow
            label="M P2 — Body Medium"
            spec="16px / 24px · Regular · Nunito Sans"
            className="font-nunito-sans text-m-p2"
          />
          <TypeRow
            label="M P3 — Body Small"
            spec="14px / 18px · Regular · Nunito Sans"
            className="font-nunito-sans text-m-p3"
          />
        </div>
      </section>

      {/* ===== COLORS ===== */}
      <section className="mb-16">
        <SectionHeader>Colors</SectionHeader>

        <div className="space-y-10">
          <ColorGroup title="Neutrals">
            <Swatch name="dark" color="bg-dark" hex="#1C1B1F" usage="Default text" />
            <Swatch name="light" color="bg-light" hex="#757575" usage="Light text" />
            <Swatch name="white" color="bg-white border border-gray-200" hex="#FFFFFF" usage="Background" />
          </ColorGroup>

          <ColorGroup title="Grey (Semantic)">
            <Swatch name="grey-200" color="bg-grey-200" hex="#EFF3F6" usage="Subtle bg" />
            <Swatch name="grey-300" color="bg-grey-300" hex="#E0E7ED" usage="Border, tags" />
            <Swatch name="grey-400" color="bg-grey-400" hex="#707581" usage="Muted text" />
          </ColorGroup>

          <ColorGroup title="Gray (Neutral)">
            <Swatch name="gray-50" color="bg-gray-50 border border-gray-200" hex="#FAFAFA" usage="Page bg" />
            <Swatch name="gray-100" color="bg-gray-100 border border-gray-200" hex="#F2F2F2" usage="Bg" />
            <Swatch name="gray-200" color="bg-gray-200" hex="#E8E8E8" usage="Border & bg" />
            <Swatch name="gray-300" color="bg-gray-300" hex="#E0E0E0" usage="Border & bg" />
          </ColorGroup>

          <ColorGroup title="Blues">
            <Swatch name="blue-50" color="bg-blue-50" hex="#E9F4FF" usage="Selection states" />
            <Swatch name="blue-100" color="bg-blue-100" hex="#BED3E9" usage="Stroke complement" />
            <Swatch name="blue-300" color="bg-blue-300" hex="#226CA7" usage="Primary / clickable" light />
            <Swatch name="blue-400" color="bg-blue-400" hex="#195586" usage="Hover states" light />
          </ColorGroup>

          <ColorGroup title="Status">
            <Swatch name="success-fill" color="bg-success-fill" hex="#ECFDF3" usage="Success bg" />
            <Swatch name="success-stroke" color="bg-success-stroke" hex="#039855" usage="Success border" light />
            <Swatch name="error-fill" color="bg-error-fill" hex="#FEF3F2" usage="Error bg" />
            <Swatch name="error-stroke" color="bg-error-stroke" hex="#D92D20" usage="Error border" light />
            <Swatch name="warning-50" color="bg-warning-50" hex="#FFFAEB" usage="Warning bg" />
            <Swatch name="warning-400" color="bg-warning-400" hex="#FDB022" usage="Warning border" />
            <Swatch name="progress" color="bg-progress" hex="#1570EF" usage="Progress indicator" light />
            <Swatch name="progress-bar" color="bg-progress-bar" hex="#0086C9" usage="Progress bar fill" light />
          </ColorGroup>

          <ColorGroup title="Brand">
            <Swatch name="brand-pink" color="bg-brand-pink" hex="#B33F93" usage="Cosmetic" light />
            <Swatch name="brand-orange" color="bg-brand-orange" hex="#EB5531" usage="Cosmetic" light />
            <Swatch name="brand-green" color="bg-brand-green" hex="#27B28D" usage="Cosmetic" light />
            <Swatch name="brand-light-blue" color="bg-brand-light-blue" hex="#09A7DF" usage="Cosmetic" light />
          </ColorGroup>
        </div>
      </section>

      {/* ===== SHADOWS ===== */}
      <section className="mb-16">
        <SectionHeader>Shadows</SectionHeader>

        <div className="flex gap-8">
          <div className="flex h-32 w-64 items-center justify-center rounded-2xl bg-white shadow-card">
            <div className="text-center">
              <p className="font-semibold text-dark">shadow-card</p>
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
        <p className="mb-6 text-p2 text-light">
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
              <span className="w-6 text-right text-p3 text-light">{step}</span>
              <div
                className="h-2 rounded-sm bg-brand-pink"
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
          <div className="flex items-start gap-2.5 rounded-2xl border border-success-800 bg-success-fill px-4 py-6">
            <span className="text-success-stroke">&#10003;</span>
            <div>
              <p className="font-semibold text-success-stroke">
                Routes generated successfully!
              </p>
              <p className="text-p2 text-success-900">
                Generated on Oct 20, 2025 at 10:42 AM
              </p>
            </div>
          </div>

          <div className="flex items-start gap-2.5 rounded-2xl border border-error-stroke bg-error-fill px-4 py-6">
            <span className="text-error-stroke">&#9888;</span>
            <p className="text-p2 font-semibold text-error-stroke">
              Unsupported format — please upload an Excel (.xlsx) file
            </p>
          </div>

          <div className="flex items-start gap-2.5 rounded-2xl border border-warning-400 bg-warning-50 px-4 py-6">
            <span className="text-warning-900">&#9888;</span>
            <p className="text-p2 font-semibold text-warning-900">
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
      <h2 className="mb-1 font-nunito text-h2 font-semibold text-dark">
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
      <h3 className="mb-3 text-p2 font-bold text-dark">{title}</h3>
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
      <p className="font-mono text-p3 text-light">{hex}</p>
      <p className="text-p3 text-light">{usage}</p>
    </div>
  );
}

function TypeRow({
  label,
  spec,
  className,
}: {
  label: string;
  spec: string;
  className: string;
}) {
  return (
    <div className="flex items-baseline gap-6">
      <p className={className}>{label}</p>
      <p className="text-p3 text-light">{spec}</p>
    </div>
  );
}
