import { SectionHeader } from '../components/SectionHeader';

export function ShadowsSection() {
  return (
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
  );
}
