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
  const [paddingTime, setPaddingTime] = useState<string | undefined>('09:30');

  return (
    <section className="mb-16">
      <SectionHeader>Time Picker</SectionHeader>
      <SectionDescription>
        A single picker for every place a time is chosen. The trigger shows the
        selected time in 12-hour form beside a clock icon, and opens one
        scrollable list of whole times. Built on{' '}
        <code className="text-p2 bg-grey-150 rounded px-1">Popover</code> so it
        looks the same in every browser.
      </SectionDescription>

      <div className="mb-10 space-y-6">
        <SpecNote title="Options">
          Every half hour of the day. A value that does not fall on the step —
          route generation staggers start times, so 8:45 and 10:05 are real — is
          added to the list so it stays visible as the selection.
        </SpecNote>
        <SpecNote title="Typing">
          The trigger is a text field as well as a dropdown, which is how a
          staggered time like 8:45 gets entered. Entry is forgiving wherever the
          intent is unambiguous — <code>9</code>, <code>9:00</code>,{' '}
          <code>9am</code>, <code>9 AM</code> and <code>09:00</code> all mean
          the same thing. Without an AM/PM the hour is assumed to fall in the
          delivery day, 8:00 AM to 7:59 PM, so <code>9</code> is 9:00 AM and{' '}
          <code>1</code> is 1:00 PM. An explicit AM/PM always wins:{' '}
          <code>1am</code> is 1:00 AM.
        </SpecNote>
        <SpecNote title="Unreadable Entry">
          Marked in red as you type and reverted to the last good value when you
          leave the field — never silently kept and never silently coerced.
          Clearing the field is treated as unfinished rather than wrong, so it
          reverts without being marked.
        </SpecNote>
        <SpecNote title="Default Value">
          When no value is provided the picker defaults to 08:00 AM.
        </SpecNote>
        <SpecNote title="Format">
          Value is stored and emitted as HH:mm (24-hour) and displayed as h:mm
          AM/PM. A value in any other shape throws rather than rendering
          something wrong.
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
          Settings. The trigger and the list options take the same inset, so an
          option&apos;s text lands on the same x as the trigger&apos;s.
        </SpecNote>
        <SpecNote title="Scrolling">
          Opening the picker scrolls the selected time to the middle of the
          list. The first and last times settle flush at the top and bottom,
          since there is nothing to scroll past.
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

        <ComponentPreview
          title="Padding"
          code={TIME_PICKER_PADDING_CODE}
          previewClassName="min-h-[300px] items-start"
        >
          <div className="flex gap-20">
            <div className="flex flex-col items-start gap-2">
              <p className="text-p3 text-grey-400">
                padding=12 — route generation
              </p>
              <TimePicker value={paddingTime} onChange={setPaddingTime} open />
            </div>
            <div className="flex flex-col items-start gap-2">
              <p className="text-p3 text-grey-400">padding=24 — Settings</p>
              <TimePicker
                value={paddingTime}
                onChange={setPaddingTime}
                padding={24}
                open
              />
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
