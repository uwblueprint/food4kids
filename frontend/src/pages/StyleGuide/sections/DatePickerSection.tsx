import { useState } from 'react';

import { DatePicker } from '@/common/components/DatePicker';

import { ComponentPreview } from '../components/ComponentPreview';
import { SectionDescription } from '../components/SectionDescription';
import { SectionHeader } from '../components/SectionHeader';
import { SectionLabel } from '../components/SectionLabel';
import { SpecNote } from '../components/SpecNote';

const DATE_PICKER_CONTROLLED_CODE = `import { useState } from 'react';
import { DatePicker } from '@/common/components';

const [date, setDate] = useState<Date | undefined>(new Date());

<DatePicker value={date} onChange={setDate} />`;

const DATE_PICKER_DISABLED_CODE = `import { DatePicker } from '@/common/components';

<DatePicker disabled />`;

export function DatePickerSection() {
  const [controlled, setControlled] = useState<Date | undefined>(new Date());

  return (
    <section className="mb-16">
      <SectionHeader>Date Picker</SectionHeader>
      <SectionDescription>
        Combines a text input with a calendar popover for structured date entry.
        The browser's native date picker indicator is hidden in favor of a
        custom calendar icon trigger. Supports uncontrolled (defaults to today)
        and controlled usage.
      </SectionDescription>

      <div className="mb-10 space-y-6">
        <SpecNote title="Input + Popover">
          Combines a native date input (type="date") with a custom calendar
          popover triggered by the calendar icon. The browser's native picker
          indicator is hidden.
        </SpecNote>
        <SpecNote title="Focus &amp; Border">
          The wrapper outline turns Blue/300 (2px) when the input is focused or
          the calendar popover is open.
        </SpecNote>
      </div>

      <SectionLabel>Usage</SectionLabel>
      <div className="space-y-6">
        <ComponentPreview title="Controlled" code={DATE_PICKER_CONTROLLED_CODE}>
          <div className="flex flex-col items-center gap-3">
            <DatePicker value={controlled} onChange={setControlled} />
            <p className="text-p3 text-grey-400">
              Selected: {controlled ? controlled.toLocaleDateString() : 'None'}
            </p>
          </div>
        </ComponentPreview>

        <ComponentPreview title="Disabled" code={DATE_PICKER_DISABLED_CODE}>
          <DatePicker disabled />
        </ComponentPreview>
      </div>
    </section>
  );
}
