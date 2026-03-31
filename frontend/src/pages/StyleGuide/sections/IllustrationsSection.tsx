import { SectionHeader } from '../components/SectionHeader';

export function IllustrationsSection() {
  return (
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
              src={
                new URL(`../../../assets/illustrations/${file}`, import.meta.url)
                  .href
              }
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
  );
}
