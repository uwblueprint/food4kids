import { useState } from 'react';

import { Calendar } from '@/common/components/Calendar';

import { SectionHeader } from '../components/SectionHeader';
import { SpecNote } from '../components/SpecNote';

export function CalendarSection() {
  const [selected, setSelected] = useState<Date | undefined>(new Date());

  return (
    <section className="mb-16">
      <SectionHeader>Calendar</SectionHeader>

      <div className="mb-10 space-y-6">
        <SpecNote title="Usage">
          Inline calendar for date selection. Used internally by DatePicker but
          can be rendered standalone. Supports single and range selection modes
          via react-day-picker.
        </SpecNote>

        <SpecNote title="Selected Date">
          The selected date is highlighted with a filled Blue/300 circle. Today's
          date uses no special highlight when unselected — only the selected date
          is colored.
        </SpecNote>

        <SpecNote title="Outside Days">
          Days from adjacent months are shown in a faded Grey/300 to provide
          context without drawing attention.
        </SpecNote>
      </div>

      <div className="border-grey-300 bg-grey-150 overflow-hidden rounded-xl border">
        <div className="divide-grey-300 grid grid-cols-1 divide-y md:grid-cols-2 md:divide-x md:divide-y-0">
          <div className="flex flex-col gap-4 p-6">
            <p className="text-p3 font-semibold tracking-wider text-blue-300 uppercase">
              Interactive
            </p>
            <Calendar
              mode="single"
              selected={selected}
              onSelect={setSelected}
            />
            <p className="text-p3 text-grey-400">
              Selected:{' '}
              {selected ? selected.toLocaleDateString() : 'None'}
            </p>
          </div>

          <div className="flex flex-col gap-4 p-6">
            <p className="text-p3 font-semibold tracking-wider text-blue-300 uppercase">
              No Selection
            </p>
            <Calendar mode="single" />
            <p className="text-p3 text-grey-400">
              Default state with no pre-selected date.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
