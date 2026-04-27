import { useState } from 'react';

import { TimePicker } from '@/common/components/TimePicker';

import { SectionHeader } from '../components/SectionHeader';
import { SpecNote } from '../components/SpecNote';

export function TimePickerSection() {
  const [time, setTime] = useState<string | undefined>('09:30');

  return (
    <section className="mb-16">
      <SectionHeader>Time Picker</SectionHeader>

      <div className="mb-10 space-y-6">
        <SpecNote title="Native Input">
          Uses a native time input (type="time") with the browser's default
          picker indicator hidden. A decorative clock icon sits on the right.
        </SpecNote>

        <SpecNote title="Default Value">
          When no value is provided the picker defaults to 08:45 AM.
        </SpecNote>

        <SpecNote title="Format">
          Value is stored and emitted as HH:mm (24-hour). Display format is
          handled by the browser's locale settings.
        </SpecNote>
      </div>

      <div className="border-grey-300 bg-grey-150 overflow-hidden rounded-xl border">
        <div className="divide-grey-300 grid grid-cols-1 divide-y md:grid-cols-3 md:divide-x md:divide-y-0">
          <div className="flex flex-col gap-4 p-6">
            <p className="text-p3 font-semibold tracking-wider text-blue-300 uppercase">
              Default (08:45)
            </p>
            <TimePicker />
            <p className="text-p3 text-grey-400">
              No value prop — defaults to 08:45.
            </p>
          </div>

          <div className="flex flex-col gap-4 p-6">
            <p className="text-p3 font-semibold tracking-wider text-blue-300 uppercase">
              Controlled
            </p>
            <TimePicker value={time} onChange={setTime} />
            <p className="text-p3 text-grey-400">
              Value: {time ?? 'None'}
            </p>
          </div>

          <div className="flex flex-col gap-4 p-6">
            <p className="text-p3 font-semibold tracking-wider text-blue-300 uppercase">
              Disabled
            </p>
            <TimePicker disabled />
            <p className="text-p3 text-grey-400">
              Input and icon both disabled.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
