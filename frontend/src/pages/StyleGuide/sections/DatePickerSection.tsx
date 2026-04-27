import { useState } from 'react';

import { DatePicker } from '@/common/components/DatePicker';

import { SectionHeader } from '../components/SectionHeader';
import { SpecNote } from '../components/SpecNote';

export function DatePickerSection() {
  const [controlled, setControlled] = useState<Date | undefined>(new Date());

  return (
    <section className="mb-16">
      <SectionHeader>Date Picker</SectionHeader>

      <div className="mb-10 space-y-6">
        <SpecNote title="Input + Popover">
          Combines a native date input (type="date") with a custom calendar
          popover triggered by the calendar icon. The browser's native picker
          indicator is hidden.
        </SpecNote>

        <SpecNote title="Default Value">
          When no value is provided, the picker defaults to today's date. The
          calendar popover opens to the month matching the current input value.
        </SpecNote>

        <SpecNote title="Focus & Border">
          The wrapper outline turns Blue/300 (2px) when the input is focused or
          the calendar popover is open.
        </SpecNote>
      </div>

      <div className="border-grey-300 bg-grey-150 overflow-hidden rounded-xl border">
        <div className="divide-grey-300 grid grid-cols-1 divide-y md:grid-cols-3 md:divide-x md:divide-y-0">
          <div className="flex flex-col gap-4 p-6">
            <p className="text-p3 font-semibold tracking-wider text-blue-300 uppercase">
              Uncontrolled (Default Today)
            </p>
            <DatePicker />
            <p className="text-p3 text-grey-400">
              No value prop — defaults to today internally.
            </p>
          </div>

          <div className="flex flex-col gap-4 p-6">
            <p className="text-p3 font-semibold tracking-wider text-blue-300 uppercase">
              Controlled
            </p>
            <DatePicker value={controlled} onChange={setControlled} />
            <p className="text-p3 text-grey-400">
              Controlled:{' '}
              {controlled ? controlled.toLocaleDateString() : 'None'}
            </p>
          </div>

          <div className="flex flex-col gap-4 p-6">
            <p className="text-p3 font-semibold tracking-wider text-blue-300 uppercase">
              Disabled
            </p>
            <DatePicker disabled />
            <p className="text-p3 text-grey-400">
              Input and calendar icon both disabled.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
