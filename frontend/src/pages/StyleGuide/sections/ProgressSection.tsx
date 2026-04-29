import { useState } from 'react';

import { Button, Progress } from '@/common/components';

import { ComponentPreview } from '../components/ComponentPreview';
import { SectionDescription } from '../components/SectionDescription';
import { SectionHeader } from '../components/SectionHeader';
import { SectionLabel } from '../components/SectionLabel';
import { SpecNote } from '../components/SpecNote';

const PROGRESS_CODE = `import { Progress } from '@/common/components';

<Progress value={40} />`;

const PROGRESS_INTERACTIVE_CODE = `import { useState } from 'react';
import { Button, Progress } from '@/common/components';

const [value, setValue] = useState(40);

<Progress value={value} />
<p>{value}%</p>
<Button variant="secondary" onClick={() => setValue((v) => Math.max(0, v - 10))}>
  −10
</Button>
<Button variant="secondary" onClick={() => setValue((v) => Math.min(100, v + 10))}>
  +10
</Button>`;

export function ProgressSection() {
  const [value, setValue] = useState(40);

  return (
    <section className="mb-16">
      <SectionHeader>Progress</SectionHeader>
      <SectionDescription>
        Linear progress bar for communicating completion percentage. Pass a{' '}
        <code className="text-p2 bg-grey-150 rounded px-1">value</code> between
        0–100; the fill transitions smoothly as the value updates.
      </SectionDescription>

      <div className="mb-10 space-y-6">
        <SpecNote title="Track &amp; Fill">
          Track: Grey/300. Fill: Blue/300. Transitions smoothly as value
          updates.
        </SpecNote>
        <SpecNote title="Value">
          Accepts a value from 0–100. Typically paired with a text label showing
          completed / total counts.
        </SpecNote>
      </div>

      <SectionLabel>Usage</SectionLabel>
      <div className="mb-8 space-y-6">
        <ComponentPreview title="Basic" code={PROGRESS_CODE}>
          <div className="w-full max-w-sm">
            <Progress value={40} />
          </div>
        </ComponentPreview>

        <ComponentPreview title="Interactive" code={PROGRESS_INTERACTIVE_CODE}>
          <div className="flex w-full max-w-sm flex-col items-center gap-3">
            <Progress value={value} className="w-full" />
            <p className="text-p3 text-grey-400">{value}%</p>
            <div className="flex gap-2">
              <Button
                variant="secondary"
                onClick={() => setValue((v) => Math.max(0, v - 10))}
              >
                −10
              </Button>
              <Button
                variant="secondary"
                onClick={() => setValue((v) => Math.min(100, v + 10))}
              >
                +10
              </Button>
            </div>
          </div>
        </ComponentPreview>
      </div>

      <SectionLabel>States</SectionLabel>
      <div className="border-grey-300 bg-grey-150 overflow-hidden rounded-xl border p-6">
        <div className="flex flex-col gap-6">
          {[0, 33, 66, 100].map((v) => (
            <div key={v} className="flex flex-col gap-2">
              <Progress value={v} />
              <p className="text-p3 text-grey-400">
                {v}%{v === 0 ? ' — Empty' : v === 100 ? ' — Complete' : ''}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
