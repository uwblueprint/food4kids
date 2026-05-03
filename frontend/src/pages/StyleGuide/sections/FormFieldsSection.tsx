import { type ReactNode, useState } from 'react';

import { Field, FieldLabel } from '@/common/components/Field';
import { FilterChip, FilterChipGroup } from '@/common/components/FilterChip';
import { Input } from '@/common/components/Input';
import { SearchBar } from '@/common/components/SearchBar';

import { ComponentPreview } from '../components/ComponentPreview';
import { CompositionTree } from '../components/CompositionTree';
import { SectionDescription } from '../components/SectionDescription';
import { SectionHeader } from '../components/SectionHeader';
import { SectionLabel } from '../components/SectionLabel';
import { SpecNote } from '../components/SpecNote';

// ---------------------------------------------------------------------------
// Composition trees
// ---------------------------------------------------------------------------

const FIELD_TREE = `Field
├─ FieldLabel
├─ Input
└─ FieldDescription`;

// ---------------------------------------------------------------------------
// Code snippets
// ---------------------------------------------------------------------------

const FIELD_BASIC_CODE = `import { Input } from '@/common/components';

<Input placeholder="Enter text here" />`;

const FIELD_COMPOSED_CODE = `import { Field, FieldLabel, Input } from '@/common/components';

<Field>
  <FieldLabel htmlFor="api-key" required>
    API Key
  </FieldLabel>
  <Input
    id="api-key"
    type="password"
    placeholder="sk-..."
    description="Your API key is stored securely."
  />
</Field>`;

const FIELD_ERROR_CODE = `import { Field, FieldLabel, Input } from '@/common/components';

<Field>
  <FieldLabel htmlFor="email" required>Email</FieldLabel>
  <Input
    id="email"
    placeholder="you@example.com"
    error="Please enter a valid email address."
  />
</Field>`;

const FIELD_CHARCOUNT_CODE = `import { Input } from '@/common/components';

const [value, setValue] = useState('');

<Input
  value={value}
  onChange={(e) => setValue(e.target.value)}
  placeholder="Type here..."
  maxCharacters={100}
  characterCount={value.length}
/>`;

const SEARCH_DEFAULT_CODE = `import { SearchBar } from '@/common/components';

<SearchBar placeholder="Search anything" />`;

const SEARCH_FILLED_CODE = `import { SearchBar } from '@/common/components';

<SearchBar variant="filled" placeholder="Search anything" />`;

const FILTER_CHIP_CODE = `import { FilterChip } from '@/common/components';

<FilterChip>Text</FilterChip>
<FilterChip selected>Selected</FilterChip>`;

const FILTER_CHIP_GROUP_CODE = `import { FilterChip, FilterChipGroup } from '@/common/components';

<FilterChipGroup label="Weekday">
  <FilterChip selected>Mon</FilterChip>
  <FilterChip>Tue</FilterChip>
  <FilterChip>Wed</FilterChip>
</FilterChipGroup>`;

// ---------------------------------------------------------------------------

export function FormFieldsSection() {
  const [textValue, setTextValue] = useState('');
  const [filledText] = useState('Lorem Ipsum is simply dummy text of th...');
  const [searchValue, setSearchValue] = useState('');
  const [filledSearchValue, setFilledSearchValue] = useState('');
  const [selectedDays, setSelectedDays] = useState<Set<string>>(
    new Set(['Wed', 'Thu'])
  );

  const toggleDay = (day: string) => {
    setSelectedDays((prev) => {
      const next = new Set(prev);
      if (next.has(day)) next.delete(day);
      else next.add(day);
      return next;
    });
  };

  const weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'];

  return (
    <section className="mb-16">
      <SectionHeader>Form Fields</SectionHeader>

      {/* ---- Spec notes ---- */}
      <div className="mb-10 space-y-6">
        <SpecNote title="Mobile Form Fields">
          Mobile form fields should span full-width of its container.
        </SpecNote>

        <SpecNote title="Border Radius">
          For radius treatment, default to 8px on all corners.
        </SpecNote>

        <SpecNote title="Padding &amp; Spacing">
          All form fields will have right and left padding equal to 12px on each
          side.
          <br />
          <br />
          Use 4px spacing between a label (such as character limits) and form
          field.
        </SpecNote>

        <SpecNote title="Text Field">
          The text field height will remain 44px throughout desktop &amp;
          tablet, and 42px throughout mobile.
          <br />
          <br />
          Stroke: 1px | Inside | Grey/300
          <br />
          Fill: Grey/100
        </SpecNote>

        <SpecNote title="Info Field (Non-editable)">
          Info fields display information that is not editable. Its height will
          adjust to the height of the text.
          <br />
          <br />
          Stroke: None
          <br />
          Fill: Grey/150
        </SpecNote>

        <SpecNote title="Typography">
          Default text &amp; label: Mobile/Paragraph/P3 | Grey/400
          <br />
          Filled-in text: Mobile/Paragraph/P2 | Grey/500
          <br />
          <br />
          The label begins turning Red at 80/100 characters for Subject fields
          and 1450/1500 for larger fields.
        </SpecNote>
      </div>

      {/* ================================================================ */}
      {/* INPUT                                                             */}
      {/* ================================================================ */}
      <SectionHeader className="mt-10">Input</SectionHeader>
      <SectionDescription>
        Composable input primitives for building form fields. Use{' '}
        <code className="text-p2 bg-grey-150 rounded px-1">Input</code>{' '}
        standalone or compose it with{' '}
        <code className="text-p2 bg-grey-150 rounded px-1">Field</code>,{' '}
        <code className="text-p2 bg-grey-150 rounded px-1">FieldLabel</code>,
        and{' '}
        <code className="text-p2 bg-grey-150 rounded px-1">
          FieldDescription
        </code>{' '}
        to build labeled, validated form fields.
      </SectionDescription>

      {/* Composition */}
      <SectionLabel>Composition</SectionLabel>
      <div className="mb-8">
        <CompositionTree tree={FIELD_TREE} />
      </div>

      {/* Usage */}
      <SectionLabel>Usage</SectionLabel>
      <div className="mb-8 space-y-6">
        <ComponentPreview title="Basic Input" code={FIELD_BASIC_CODE}>
          <div className="w-80">
            <Input placeholder="Enter text here" />
          </div>
        </ComponentPreview>

        <ComponentPreview
          title="With Field and Label"
          code={FIELD_COMPOSED_CODE}
        >
          <div className="w-80">
            <Field>
              <FieldLabel htmlFor="sg-field-demo" required>
                API Key
              </FieldLabel>
              <Input
                id="sg-field-demo"
                type="password"
                placeholder="sk-..."
                description="Your API key is stored securely."
              />
            </Field>
          </div>
        </ComponentPreview>

        <ComponentPreview title="With Validation Error" code={FIELD_ERROR_CODE}>
          <div className="w-80">
            <Field>
              <FieldLabel htmlFor="sg-field-error" required>
                Email
              </FieldLabel>
              <Input
                id="sg-field-error"
                placeholder="you@example.com"
                error="Please enter a valid email address."
              />
            </Field>
          </div>
        </ComponentPreview>

        <ComponentPreview title="Character Count" code={FIELD_CHARCOUNT_CODE}>
          <div className="w-80">
            <Field>
              <FieldLabel htmlFor="sg-charcount">Subject</FieldLabel>
              <Input
                id="sg-charcount"
                placeholder="Type to see character count..."
                value={textValue}
                onChange={(e) => setTextValue(e.target.value)}
                maxCharacters={100}
                characterCount={textValue.length}
              />
            </Field>
          </div>
        </ComponentPreview>
      </div>

      {/* States */}
      <SectionLabel>States</SectionLabel>
      <div className="border-grey-300 bg-grey-150 overflow-hidden rounded-xl border">
        <div className="divide-grey-300 grid grid-cols-1 divide-y md:grid-cols-3 md:divide-x md:divide-y-0">
          {/* Desktop states */}
          <div className="space-y-8 p-6">
            <p className="text-p3 mb-4 font-semibold tracking-wider text-blue-300 uppercase">
              Desktop
            </p>

            <FormFieldDemo label="Default State">
              <Field>
                <FieldLabel htmlFor="tf-default">Label</FieldLabel>
                <Input
                  id="tf-default"
                  placeholder="Enter text here"
                  description="Some information about the field"
                />
              </Field>
            </FormFieldDemo>

            <FormFieldDemo label="Active State (simulated)">
              <Field>
                <FieldLabel htmlFor="tf-active">Label</FieldLabel>
                <Input
                  id="tf-active"
                  placeholder="Enter text here"
                  description="Some information about the field"
                  className="outline-2 outline-blue-300"
                />
              </Field>
            </FormFieldDemo>

            <FormFieldDemo label="Error State">
              <Field>
                <FieldLabel htmlFor="tf-error">Label</FieldLabel>
                <Input
                  id="tf-error"
                  placeholder="Enter text here"
                  error="Some information about the field"
                />
              </Field>
            </FormFieldDemo>

            <FormFieldDemo label="Disabled State">
              <Field>
                <FieldLabel htmlFor="tf-disabled" className="opacity-50">
                  Label
                </FieldLabel>
                <Input
                  id="tf-disabled"
                  placeholder="Enter text here"
                  disabled
                />
              </Field>
            </FormFieldDemo>
          </div>

          {/* Mobile + character count */}
          <div className="space-y-8 p-6">
            <p className="text-p3 mb-4 font-semibold tracking-wider text-blue-300 uppercase">
              Mobile
            </p>

            <FormFieldDemo label="Default State">
              <Input
                placeholder="Enter text here"
                maxCharacters={100}
                characterCount={0}
              />
            </FormFieldDemo>

            <FormFieldDemo label="Filled-in State (threshold warning)">
              <Input
                value={filledText}
                readOnly
                maxCharacters={100}
                characterCount={100}
              />
            </FormFieldDemo>
          </div>

          {/* Info field */}
          <div className="space-y-8 p-6">
            <p className="text-p3 mb-4 font-semibold tracking-wider text-blue-300 uppercase">
              Info Field (Non-Editable)
            </p>

            <FormFieldDemo label="Info Field (White Background Added for Contrast)">
              <div className="rounded-lg bg-white p-4">
                <Field>
                  <FieldLabel htmlFor="tf-info">Address</FieldLabel>
                  <Input
                    id="tf-info"
                    value="3245 Spruce Street West, Kitchener, ON, M1W 1X1"
                    readOnly
                    className="bg-grey-150 cursor-default outline-none"
                  />
                </Field>
              </div>
            </FormFieldDemo>
          </div>
        </div>
      </div>

      {/* ================================================================ */}
      {/* SEARCH                                                            */}
      {/* ================================================================ */}
      <SectionHeader className="mt-10">Search</SectionHeader>
      <SectionDescription>
        A search input with a leading icon. Use the{' '}
        <code className="text-p2 bg-grey-150 rounded px-1">
          variant="filled"
        </code>{' '}
        prop for use on grey backgrounds where the default outlined style
        provides insufficient contrast.
      </SectionDescription>

      <SectionLabel>Usage</SectionLabel>
      <div className="mb-8 space-y-6">
        <ComponentPreview title="Outlined (Default)" code={SEARCH_DEFAULT_CODE}>
          <div className="w-full max-w-sm">
            <SearchBar placeholder="Search anything" />
          </div>
        </ComponentPreview>

        <ComponentPreview title="Filled" code={SEARCH_FILLED_CODE}>
          <div className="w-full max-w-sm">
            <SearchBar variant="filled" placeholder="Search anything" />
          </div>
        </ComponentPreview>
      </div>

      <SectionLabel>States</SectionLabel>
      <div className="border-grey-300 bg-grey-150 overflow-hidden rounded-xl border">
        <div className="divide-grey-300 grid grid-cols-1 divide-y md:grid-cols-2 md:divide-x md:divide-y-0">
          <div className="space-y-8 p-6">
            <p className="text-p3 mb-4 font-semibold tracking-wider text-blue-300 uppercase">
              Outlined (Default)
            </p>

            <FormFieldDemo label="Default State">
              <SearchBar placeholder="Search anything" />
            </FormFieldDemo>

            <FormFieldDemo label="Active State (Interactive)">
              <SearchBar
                placeholder="Search anything"
                value={searchValue}
                onChange={(e) => setSearchValue(e.target.value)}
              />
            </FormFieldDemo>
          </div>

          <div className="space-y-8 p-6">
            <p className="text-p3 mb-4 font-semibold tracking-wider text-blue-300 uppercase">
              Filled Variant
            </p>

            <FormFieldDemo label="Filled State">
              <SearchBar
                variant="filled"
                placeholder="Search anything"
                value={filledSearchValue}
                onChange={(e) => setFilledSearchValue(e.target.value)}
              />
            </FormFieldDemo>
          </div>
        </div>
      </div>

      {/* ================================================================ */}
      {/* FILTER CHIPS                                                      */}
      {/* ================================================================ */}
      <SectionHeader className="mt-10">Filtration Chips</SectionHeader>
      <SectionDescription>
        Toggle chips for filtering lists. Use{' '}
        <code className="text-p2 bg-grey-150 rounded px-1">FilterChip</code>{' '}
        standalone or group multiple chips with{' '}
        <code className="text-p2 bg-grey-150 rounded px-1">
          FilterChipGroup
        </code>
        . When multiple groups appear on a page, they are separated by a
        full-width Grey/300 line.
      </SectionDescription>

      <SectionLabel>Usage</SectionLabel>
      <div className="mb-8 space-y-6">
        <ComponentPreview title="Chip" code={FILTER_CHIP_CODE}>
          <div className="flex gap-3">
            <FilterChip>Text</FilterChip>
            <FilterChip selected>Selected</FilterChip>
          </div>
        </ComponentPreview>

        <ComponentPreview title="Chip Group" code={FILTER_CHIP_GROUP_CODE}>
          <FilterChipGroup label="Weekday">
            {['Mon', 'Tue', 'Wed'].map((day) => (
              <FilterChip key={day} selected={day === 'Mon'}>
                {day}
              </FilterChip>
            ))}
          </FilterChipGroup>
        </ComponentPreview>
      </div>

      <SectionLabel>States</SectionLabel>
      <div className="border-grey-300 bg-grey-150 overflow-hidden rounded-xl border">
        <div className="divide-grey-300 grid grid-cols-1 divide-y md:grid-cols-2 md:divide-x md:divide-y-0">
          <div className="space-y-8 p-6">
            <p className="text-p3 mb-4 font-semibold tracking-wider text-blue-300 uppercase">
              Chip States
            </p>

            <div className="flex flex-wrap gap-4">
              <FormFieldDemo label="Default">
                <FilterChip>Text</FilterChip>
              </FormFieldDemo>

              <FormFieldDemo label="Selected">
                <FilterChip selected>Text</FilterChip>
              </FormFieldDemo>
            </div>

            <div className="flex flex-wrap gap-4">
              <FormFieldDemo label="Hover (simulated)">
                <FilterChip className="!shadow-harsh">Text</FilterChip>
              </FormFieldDemo>

              <FormFieldDemo label="Selected Hover (simulated)">
                <FilterChip selected className="!shadow-harsh">
                  Text
                </FilterChip>
              </FormFieldDemo>
            </div>
          </div>

          <div className="space-y-8 p-6">
            <p className="text-p3 mb-4 font-semibold tracking-wider text-blue-300 uppercase">
              Chip Group
            </p>

            <FilterChipGroup label="Weekday">
              {weekdays.map((day) => (
                <FilterChip
                  key={day}
                  selected={selectedDays.has(day)}
                  onClick={() => toggleDay(day)}
                >
                  {day}
                </FilterChip>
              ))}
            </FilterChipGroup>

            <FilterChipGroup label="Time of Day" showDelimiter>
              {['Morning', 'Afternoon', 'Evening'].map((time) => (
                <FilterChip key={time}>{time}</FilterChip>
              ))}
            </FilterChipGroup>
          </div>
        </div>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------

function FormFieldDemo({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-2">
      {children}
      <p className="text-p3 text-grey-400">{label}</p>
    </div>
  );
}
