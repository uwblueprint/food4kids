import { SectionHeader } from '../components/SectionHeader';

export function LogosSection() {
  return (
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
              src={
                new URL(`../../../assets/logos/${file}`, import.meta.url).href
              }
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
  );
}
