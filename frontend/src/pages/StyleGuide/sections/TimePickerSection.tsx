import { useState } from 'react';

import { TimePicker } from '@/common/components/TimePicker';

import { ComponentPreview } from '../components/ComponentPreview';
import { SectionDescription } from '../components/SectionDescription';
import { SectionHeader } from '../components/SectionHeader';
import { SectionLabel } from '../components/SectionLabel';
import { SpecNote } from '../components/SpecNote';

const TIME_PICKER_CONTROLLED_CODE = `import { useState } from 'react';
import { TimePicker } from '@/common/components';

const [time, setTime] = useState<string | undefined>('09:30');

<TimePicker value={time} onChange={setTime} />`;

const TIME_PICKER_PADDING_CODE = `import { TimePicker } from '@/common/components';

// Route generation — 12px, matching the table's other fields (the default)
<TimePicker value={time} onChange={setTime} />

// Settings — 24px, matching the wider buttons on that page
<TimePicker value={time} onChange={setTime} padding={24} />`;

const TIME_PICKER_DISABLED_CODE = `import { TimePicker } from '@/common/components';

<TimePicker disabled />`;

export function TimePickerSection() {
  const [time, setTime] = useState<string | undefined>('09:30');
  const [settingsTime, setSettingsTime] = useState<string | undefined>('09:30');

  return (
    <section className="mb-16">
      <SectionHeader>Time Picker</SectionHeader>
      <SectionDescription>
        A single picker for every place a time is chosen. The trigger shows the
        selected time in 12-hour form beside a clock icon, and opens a popover
        with hour / minute / AM-PM columns. Built on{' '}
        <code className="text-p2 bg-grey-150 rounded px-1">Popover</code> so it
        looks the same in every browser.
      </SectionDescription>

      <div className="mb-10 space-y-6">
        <SpecNote title="Default Value">
          When no value is provided the picker defaults to 08:00 AM.
        </SpecNote>
        <SpecNote title="Format">
          Value is stored and emitted as HH:mm (24-hour) and displayed as h:mm
          AM/PM. Minutes snap to five-minute increments.
        </SpecNote>
        <SpecNote title="Icon">
          Always a clock — never a dropdown arrow, even inside the
          route-generation table where every other field carries an arrow.
        </SpecNote>
        <SpecNote title="Padding">
          A dropdown&apos;s left padding follows the button it opens from, so
          the value is a prop rather than a per-page override:{' '}
          <code className="text-p2 bg-grey-150 rounded px-1">12</code> (default)
          in route generation,{' '}
          <code className="text-p2 bg-grey-150 rounded px-1">24</code> in
          Settings.
        </SpecNote>
      </div>

      <SectionLabel>Usage</SectionLabel>
      <div className="space-y-6">
        <ComponentPreview title="Controlled" code={TIME_PICKER_CONTROLLED_CODE}>
          <div className="flex flex-col items-center gap-3">
            <TimePicker value={time} onChange={setTime} />
            <p className="text-p3 text-grey-400">Value: {time ?? 'None'}</p>
          </div>
        </ComponentPreview>

        <ComponentPreview title="Padding" code={TIME_PICKER_PADDING_CODE}>
          <div className="flex flex-col items-center gap-6">
            <div className="flex flex-col items-center gap-2">
              <TimePicker value={settingsTime} onChange={setSettingsTime} />
              <p className="text-p3 text-grey-400">
                padding=12 — route generation
              </p>
            </div>
            <div className="flex flex-col items-center gap-2">
              <TimePicker
                value={settingsTime}
                onChange={setSettingsTime}
                padding={24}
              />
              <p className="text-p3 text-grey-400">padding=24 — Settings</p>
            </div>
          </div>
        </ComponentPreview>

        <ComponentPreview title="Disabled" code={TIME_PICKER_DISABLED_CODE}>
          <TimePicker disabled />
        </ComponentPreview>
      </div>
    </section>
  );
}
