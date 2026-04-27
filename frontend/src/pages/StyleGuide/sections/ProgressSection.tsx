import { useState } from 'react';

import { Button, Progress } from '@/common/components';

import { SectionHeader } from '../components/SectionHeader';
import { SpecNote } from '../components/SpecNote';

export function ProgressSection() {
  const [value, setValue] = useState(40);

  return (
    <section className="mb-16">
      <SectionHeader>Progress</SectionHeader>

      <div className="mb-10 space-y-6">
        <SpecNote title="Usage">
          Displays a linear progress bar to communicate completion percentage.
          Used on the route generation screen to show how many route groups have
          been processed.
        </SpecNote>

        <SpecNote title="Track & Fill">
          Track: Grey/300. Fill: Blue/300. Transitions smoothly as value
          updates.
        </SpecNote>

        <SpecNote title="Value">
          Accepts a value from 0–100. Typically paired with a text label showing
          completed / total counts.
        </SpecNote>
      </div>

      <div className="border-grey-300 bg-grey-150 overflow-hidden rounded-xl border">
        <div className="divide-grey-300 grid grid-cols-1 divide-y md:grid-cols-2 md:divide-x md:divide-y-0">
          <div className="flex flex-col gap-6 p-6">
            <p className="text-p3 font-semibold tracking-wider text-blue-300 uppercase">
              Static States
            </p>

            <div className="flex flex-col gap-2">
              <Progress value={0} />
              <p className="text-p3 text-grey-400">0% — Empty</p>
            </div>

            <div className="flex flex-col gap-2">
              <Progress value={33} />
              <p className="text-p3 text-grey-400">33%</p>
            </div>

            <div className="flex flex-col gap-2">
              <Progress value={66} />
              <p className="text-p3 text-grey-400">66%</p>
            </div>

            <div className="flex flex-col gap-2">
              <Progress value={100} />
              <p className="text-p3 text-grey-400">100% — Complete</p>
            </div>
          </div>

          <div className="flex flex-col gap-6 p-6">
            <p className="text-p3 font-semibold tracking-wider text-blue-300 uppercase">
              Interactive
            </p>

            <div className="flex flex-col gap-3">
              <Progress value={value} className="h-2 w-full" />
              <p className="text-p3 text-center text-grey-400">{value}%</p>
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
          </div>
        </div>
      </div>
    </section>
  );
}
