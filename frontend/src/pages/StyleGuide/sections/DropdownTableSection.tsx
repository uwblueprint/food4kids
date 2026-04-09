import { useState } from 'react';

import { DropdownTable, type DropdownTableRow } from '@/common/components';

import { SectionHeader } from '../components/SectionHeader';
import { SpecNote } from '../components/SpecNote';

const MOCK_OPTIONS = [
  { label: 'Column A', value: 'col_a' },
  { label: 'Column B', value: 'col_b' },
  { label: 'Column C', value: 'col_c' },
];

const INITIAL_ROWS: DropdownTableRow[] = [
  {
    label: 'School Name / Child Last Name',
    required: true,
    options: MOCK_OPTIONS,
  },
  { label: 'Address', required: true, options: MOCK_OPTIONS },
  { label: 'Delivery Group', required: true, options: MOCK_OPTIONS },
  { label: 'Phone Number', required: true, options: MOCK_OPTIONS },
  { label: 'Number of Children', required: true, options: MOCK_OPTIONS },
  { label: 'Food Restrictions', required: true, options: MOCK_OPTIONS },
];

export function DropdownTableSection() {
  const [values, setValues] = useState<Record<number, string>>({});

  const rows: DropdownTableRow[] = INITIAL_ROWS.map((row, i) => ({
    ...row,
    value: values[i],
    onValueChange: (v) => setValues((prev) => ({ ...prev, [i]: v })),
  }));

  return (
    <section className="mb-16">
      <SectionHeader>Tables</SectionHeader>
      <SpecNote title="Table Dropdown">
        Customize dropdown options here.
      </SpecNote>
      <br />
      <DropdownTable rows={rows} />
    </section>
  );
}
