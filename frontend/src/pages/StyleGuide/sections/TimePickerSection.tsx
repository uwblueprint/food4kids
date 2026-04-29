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

const TIME_PICKER_DISABLED_CODE = `import { TimePicker } from '@/common/components';

<TimePicker disabled />`;

export function TimePickerSection() {
  const [time, setTime] = useState<string | undefined>('09:30');

  return (
    <section className="mb-16">
      <SectionHeader>Time Picker</SectionHeader>
      <SectionDescription>
        Native time input (HH:mm, 24-hour) with the browser's default indicator
        hidden and a decorative clock icon on the right. Integrates with{' '}
        <code className="text-p2 rounded bg-grey-150 px-1">Input</code> for
        consistent styling and focus behavior.
      </SectionDescription>

      <div className="mb-10 space-y-6">
        <SpecNote title="Default Value">
          When no value is provided the picker defaults to 08:45 AM.
        </SpecNote>
        <SpecNote title="Format">
          Value is stored and emitted as HH:mm (24-hour). Display format is
          handled by the browser's locale settings.
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

        <ComponentPreview title="Disabled" code={TIME_PICKER_DISABLED_CODE}>
          <TimePicker disabled />
        </ComponentPreview>
      </div>
    </section>
  );
}
