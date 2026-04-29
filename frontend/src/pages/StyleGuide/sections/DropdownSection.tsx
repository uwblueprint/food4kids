import { useState } from 'react';

import {
  Dropdown,
  DropdownContent,
  DropdownItem,
  DropdownTrigger,
  DropdownValue,
} from '@/common/components/Dropdown';
import { Field, FieldDescription, FieldLabel } from '@/common/components/Field';
import { ComponentPreview } from '../components/ComponentPreview';
import { CompositionTree } from '../components/CompositionTree';
import { SectionDescription } from '../components/SectionDescription';
import { SectionHeader } from '../components/SectionHeader';

const DROPDOWN_TREE = `Dropdown
├─ DropdownTrigger
│   └─ DropdownValue
└─ DropdownContent
    └─ DropdownItem`;

const DROPDOWN_BASIC_CODE = `import {
  Dropdown,
  DropdownTrigger,
  DropdownValue,
  DropdownContent,
  DropdownItem,
} from '@/common/components';

<Dropdown value={value} onValueChange={setValue}>
  <DropdownTrigger>
    <DropdownValue placeholder="Select an option..." />
  </DropdownTrigger>
  <DropdownContent>
    <DropdownItem value="opt1">Option 1</DropdownItem>
    <DropdownItem value="opt2">Option 2</DropdownItem>
    <DropdownItem value="opt3">Option 3</DropdownItem>
  </DropdownContent>
</Dropdown>`;

const DROPDOWN_FIELD_CODE = `import {
  Dropdown,
  DropdownContent,
  DropdownItem,
  DropdownTrigger,
  DropdownValue,
  Field,
  FieldDescription,
  FieldLabel,
} from '@/common/components';

<Field>
  <FieldLabel>Driver</FieldLabel>
  <Dropdown value={value} onValueChange={setValue}>
    <DropdownTrigger>
      <DropdownValue placeholder="Select a driver..." />
    </DropdownTrigger>
    <DropdownContent>
      <DropdownItem value="marcus">Marcus Smith</DropdownItem>
      <DropdownItem value="sarah">Sarah Lee</DropdownItem>
    </DropdownContent>
  </Dropdown>
  <FieldDescription>Last driven by: John Doe</FieldDescription>
</Field>`;

const demoOptions = [
  { label: 'Option 1', value: 'opt1' },
  { label: 'Option 2', value: 'opt2' },
  { label: 'Option 3', value: 'opt3' },
];

export function DropdownSection() {
  const [value, setValue] = useState<string | undefined>();

  return (
    <section className="mb-16">
      <SectionHeader>Dropdown</SectionHeader>
      <SectionDescription>
        Composable dropdown built on Radix UI Select. Use{' '}
        <code className="text-p2 rounded bg-grey-150 px-1">DropdownTrigger</code>,{' '}
        <code className="text-p2 rounded bg-grey-150 px-1">DropdownContent</code>, and{' '}
        <code className="text-p2 rounded bg-grey-150 px-1">DropdownItem</code> to assemble
        flexible select menus. Wrap in{' '}
        <code className="text-p2 rounded bg-grey-150 px-1">Field</code> to add a label and
        helper text.
      </SectionDescription>

      {/* Composition */}
      <p className="text-p3 mb-2 font-semibold tracking-wider text-grey-400 uppercase">
        Composition
      </p>
      <div className="mb-8 space-y-6">
        <CompositionTree tree={DROPDOWN_TREE} />
      </div>

      {/* Usage */}
      <p className="text-p3 mb-2 font-semibold tracking-wider text-grey-400 uppercase">
        Usage
      </p>
      <div className="mb-8 space-y-6">
        <ComponentPreview title="Basic Usage" code={DROPDOWN_BASIC_CODE}>
          <div className="w-64">
            <Dropdown value={value} onValueChange={setValue}>
              <DropdownTrigger>
                <DropdownValue placeholder="Select an option..." />
              </DropdownTrigger>
              <DropdownContent>
                {demoOptions.map((opt) => (
                  <DropdownItem key={opt.value} value={opt.value}>
                    {opt.label}
                  </DropdownItem>
                ))}
              </DropdownContent>
            </Dropdown>
          </div>
        </ComponentPreview>

        <ComponentPreview title="With Field and Description" code={DROPDOWN_FIELD_CODE}>
          <div className="w-64">
            <Field>
              <FieldLabel>Driver</FieldLabel>
              <Dropdown value={value} onValueChange={setValue}>
                <DropdownTrigger>
                  <DropdownValue placeholder="Select a driver..." />
                </DropdownTrigger>
                <DropdownContent>
                  {demoOptions.map((opt) => (
                    <DropdownItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </DropdownItem>
                  ))}
                </DropdownContent>
              </Dropdown>
              <FieldDescription>Last driven by: John Doe</FieldDescription>
            </Field>
          </div>
        </ComponentPreview>
      </div>

      {/* States */}
      <p className="text-p3 mb-2 font-semibold tracking-wider text-grey-400 uppercase">
        States
      </p>
      <div className="border-grey-300 bg-grey-150 overflow-hidden rounded-xl border">
        <div className="divide-grey-300 grid grid-cols-1 divide-y md:grid-cols-2 md:divide-x md:divide-y-0">
          <div className="space-y-8 p-6">
            <p className="text-p3 mb-4 font-semibold tracking-wider text-blue-300 uppercase">
              Error State
            </p>
            <Field>
              <FieldLabel>Driver</FieldLabel>
              <Dropdown>
                <DropdownTrigger className="ring-red focus:ring-red data-[state=open]:ring-red">
                  <DropdownValue placeholder="Dropdown Selection" />
                </DropdownTrigger>
                <DropdownContent>
                  {demoOptions.map((opt) => (
                    <DropdownItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </DropdownItem>
                  ))}
                </DropdownContent>
              </Dropdown>
              <FieldDescription error>Some information about the dropdown</FieldDescription>
            </Field>
          </div>
          <div className="space-y-8 p-6">
            <p className="text-p3 mb-4 font-semibold tracking-wider text-blue-300 uppercase">
              Disabled State
            </p>
            <Field>
              <FieldLabel className="opacity-50">Driver</FieldLabel>
              <Dropdown disabled>
                <DropdownTrigger>
                  <DropdownValue placeholder="Dropdown Selection" />
                </DropdownTrigger>
                <DropdownContent>
                  {demoOptions.map((opt) => (
                    <DropdownItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </DropdownItem>
                  ))}
                </DropdownContent>
              </Dropdown>
              <FieldDescription className="opacity-50">
                Some information about the dropdown
              </FieldDescription>
            </Field>
          </div>
        </div>
      </div>
    </section>
  );
}
