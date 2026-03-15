import { SectionHeader } from '../components/SectionHeader';

export function BannersSection() {
  return (
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
  );
}
