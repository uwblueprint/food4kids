import { type ReactNode, useState } from 'react';

import { Dropdown } from '@/common/components/Dropdown';
import { FilterChip, FilterChipGroup } from '@/common/components/FilterChip';
import { SearchBar } from '@/common/components/SearchBar';
import { TextField } from '@/common/components/TextField';

import { SectionHeader } from '../components/SectionHeader';
import { SpecNote } from '../components/SpecNote';

export function FormFieldsSection() {
  const [textValue, setTextValue] = useState('');
  const [filledText] = useState('Lorem Ipsum is simply dummy text of th...');
  const [dropdownValue, setDropdownValue] = useState<string | undefined>();
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

  const demoOptions = [
    { label: 'Option 1', value: 'opt1' },
    { label: 'Option 2', value: 'opt2' },
    { label: 'Option 3', value: 'opt3' },
  ];

  const weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'];

  return (
    <section className="mb-16">
      <SectionHeader>Form Fields</SectionHeader>

      {/* ---- Spec notes ---- */}
      <div className="mb-10 space-y-6">
        <SpecNote title="Mobile Form Fields">
          Mobile for fields should span full-width of its container.
        </SpecNote>

        <SpecNote title="Border Radius">
          For radius treatment, default to 8px on all corners.
        </SpecNote>

        <SpecNote title="Padding & Spacing">
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

      {/* ---- Text Field demos ---- */}
      <div className="border-grey-300 bg-grey-150 overflow-hidden rounded-xl border">
        <div className="divide-grey-300 grid grid-cols-1 divide-y md:grid-cols-3 md:divide-x md:divide-y-0">
          {/* Column 1: Desktop Text Field states */}
          <div className="space-y-8 p-6">
            <p className="text-p3 mb-4 font-semibold tracking-wider text-blue-300 uppercase">
              Desktop Text Field
            </p>

            <FormFieldDemo label="Default State">
              <TextField
                label="Label"
                placeholder="Enter text here"
                helperText="Some information about the field"
              />
            </FormFieldDemo>

            <FormFieldDemo label="Active State">
              <TextField
                label="Label"
                placeholder="Enter text here"
                helperText="Some information about the field"
                className="[&_input]:border-blue-300 [&_input]:ring-1 [&_input]:ring-blue-300"
              />
            </FormFieldDemo>

            <FormFieldDemo label="Error State">
              <TextField
                label="Label"
                placeholder="Enter text here"
                error="Some information about the field"
              />
            </FormFieldDemo>

            <FormFieldDemo label="Disabled State">
              <TextField
                label="Label"
                placeholder="Enter text here"
                helperText="Some information about the field"
                disabled
              />
            </FormFieldDemo>
          </div>

          {/* Column 2: Mobile Text Field + Character Count */}
          <div className="space-y-8 p-6">
            <p className="text-p3 mb-4 font-semibold tracking-wider text-blue-300 uppercase">
              Mobile Text Field
            </p>

            <FormFieldDemo label="Default State">
              <TextField
                placeholder="Enter text here"
                maxCharacters={100}
                characterCount={0}
              />
            </FormFieldDemo>

            <FormFieldDemo label="Filled-in State">
              <TextField
                value={filledText}
                readOnly
                maxCharacters={100}
                characterCount={80}
              />
            </FormFieldDemo>

            <FormFieldDemo label="Interactive Demo">
              <TextField
                label="Label"
                placeholder="Type to see character count..."
                value={textValue}
                onChange={(e) => setTextValue(e.target.value)}
                maxCharacters={100}
                characterCount={textValue.length}
                helperText="Try typing 80+ characters"
              />
            </FormFieldDemo>
          </div>

          {/* Column 3: Info Field (Non-editable) + Example */}
          <div className="space-y-8 p-6">
            <p className="text-p3 mb-4 font-semibold tracking-wider text-blue-300 uppercase">
              Info Field (Non-Editable)
            </p>

            <FormFieldDemo label="Info Field (White Background Added for Contrast)">
              <div className="rounded-lg bg-white p-4">
                <TextField
                  info
                  label="Address"
                  value="3245 Spruce Street West, Kitchener, ON, M1W 1X1"
                />
              </div>
            </FormFieldDemo>
          </div>
        </div>
      </div>

      {/* ---- Dropdown demos ---- */}
      <h3 className="mt-10 mb-1">Dropdown</h3>
      <hr className="border-grey-300 mb-6" />

      <div className="border-grey-300 bg-grey-150 overflow-hidden rounded-xl border">
        <div className="divide-grey-300 grid grid-cols-1 divide-y md:grid-cols-3 md:divide-x md:divide-y-0">
          {/* Column 1: Default + Active */}
          <div className="space-y-8 p-6">
            <p className="text-p3 mb-4 font-semibold tracking-wider text-blue-300 uppercase">
              Dropdown States
            </p>

            <FormFieldDemo label="Default State">
              <Dropdown
                label="Driver"
                placeholder="Dropdown Selection"
                options={demoOptions}
                helperText="Some information about the dropdown"
              />
            </FormFieldDemo>

            <FormFieldDemo label="Interactive Demo">
              <Dropdown
                label="Driver"
                placeholder="Dropdown Selection"
                options={demoOptions}
                value={dropdownValue}
                onValueChange={setDropdownValue}
                helperText="Click to open and select an option"
              />
            </FormFieldDemo>
          </div>

          {/* Column 2: Error + Disabled */}
          <div className="space-y-8 p-6">
            <p className="text-p3 mb-4 font-semibold tracking-wider text-blue-300 uppercase">
              Error & Disabled
            </p>

            <FormFieldDemo label="Error State">
              <Dropdown
                label="Driver"
                placeholder="Dropdown Selection"
                options={demoOptions}
                error="Some information about the dropdown"
              />
            </FormFieldDemo>

            <FormFieldDemo label="Disabled State">
              <Dropdown
                label="Driver"
                placeholder="Dropdown Selection"
                options={demoOptions}
                helperText="Some information about the dropdown"
                disabled
              />
            </FormFieldDemo>
          </div>

          {/* Column 3: Spec notes */}
          <div className="space-y-4 p-6">
            <p className="text-p3 mb-4 font-semibold tracking-wider text-blue-300 uppercase">
              Dropdown Spec
            </p>
            <p className="text-p2 text-grey-500">
              The dropdown options will fill the width of the clickable
              container above them.
            </p>
            <p className="text-p2 text-grey-500">
              Follow the right for the correct padding and margin on this
              separate component.
            </p>
            <p className="text-p2 text-grey-500">
              The blue option will be whatever option is currently
              selected/shown in the dropdown.
            </p>
          </div>
        </div>
      </div>

      {/* ---- Search demos ---- */}
      <h3 className="mt-10 mb-1">Search</h3>
      <hr className="border-grey-300 mb-6" />

      <div className="border-grey-300 bg-grey-150 overflow-hidden rounded-xl border">
        <div className="divide-grey-300 grid grid-cols-1 divide-y md:grid-cols-2 md:divide-x md:divide-y-0">
          {/* Default state */}
          <div className="space-y-8 p-6">
            <p className="text-p3 mb-4 font-semibold tracking-wider text-blue-300 uppercase">
              Search States
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

          {/* Filled state */}
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

            <p className="text-p2 text-grey-500">
              The purpose of the filled search bar compared to the outlined
              search bar is because there are instances in the designs where we
              needed a search bar on a contrasting background.
            </p>
          </div>
        </div>
      </div>

      {/* ---- Filter Chips demos ---- */}
      <h3 className="mt-10 mb-1">Filtration Chips</h3>
      <hr className="border-grey-300 mb-6" />

      <div className="border-grey-300 bg-grey-150 overflow-hidden rounded-xl border">
        <div className="divide-grey-300 grid grid-cols-1 divide-y md:grid-cols-2 md:divide-x md:divide-y-0">
          {/* Chip states */}
          <div className="space-y-8 p-6">
            <p className="text-p3 mb-4 font-semibold tracking-wider text-blue-300 uppercase">
              Chip States
            </p>

            <div className="flex flex-wrap gap-4">
              <FormFieldDemo label="Default State">
                <FilterChip>Text</FilterChip>
              </FormFieldDemo>

              <FormFieldDemo label="Selected State">
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

            <p className="text-p2 text-grey-500">
              These are chips used to filter as seen on desktop views. Clicking
              a chip in default state will convert it to its selected state, and
              then clicking again will revert it back to the default state.
            </p>
          </div>

          {/* Chip group */}
          <div className="space-y-8 p-6">
            <p className="text-p3 mb-4 font-semibold tracking-wider text-blue-300 uppercase">
              Filtration Chip Group
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

            <p className="text-p2 text-grey-500">
              Above you&apos;ll see how to set up a filtration chip group. If
              there are multiple of these in a page, they should be delimited by
              a full-width Grey/300 1px line.
            </p>

            {/* Second group to show delimiter */}
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
