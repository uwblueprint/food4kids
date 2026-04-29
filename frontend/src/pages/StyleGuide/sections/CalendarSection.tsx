import { useState } from 'react';

import { Calendar } from '@/common/components/Calendar';

import { ComponentPreview } from '../components/ComponentPreview';
import { SectionDescription } from '../components/SectionDescription';
import { SectionHeader } from '../components/SectionHeader';
import { SpecNote } from '../components/SpecNote';

const CALENDAR_CONTROLLED_CODE = `import { useState } from 'react';
import { Calendar } from '@/common/components';

const [selected, setSelected] = useState<Date | undefined>(new Date());

<Calendar mode="single" selected={selected} onSelect={setSelected} />`;


export function CalendarSection() {
  const [selected, setSelected] = useState<Date | undefined>(new Date());

  return (
    <section className="mb-16">
      <SectionHeader>Calendar</SectionHeader>
      <SectionDescription>
        Inline calendar for date selection built on react-day-picker. Used
        internally by DatePicker but can be rendered standalone. Supports single
        and range selection modes.
      </SectionDescription>

      <div className="mb-10 space-y-6">
        <SpecNote title="Selected Date">
          The selected date is highlighted with a filled Blue/300 circle.
          Today's date uses no special highlight when unselected — only the
          selected date is colored.
        </SpecNote>
        <SpecNote title="Outside Days">
          Days from adjacent months are shown in a faded Grey/300 to provide
          context without drawing attention.
        </SpecNote>
      </div>

      <p className="text-p3 mb-2 font-semibold tracking-wider text-grey-400 uppercase">
        Usage
      </p>
      <div className="space-y-6">
        <ComponentPreview title="Controlled" code={CALENDAR_CONTROLLED_CODE}>
          <div className="flex flex-col items-center gap-3">
            <Calendar mode="single" selected={selected} onSelect={setSelected} />
            <p className="text-p3 text-grey-400">
              Selected: {selected ? selected.toLocaleDateString() : 'None'}
            </p>
          </div>
        </ComponentPreview>

      </div>
    </section>
  );
}
