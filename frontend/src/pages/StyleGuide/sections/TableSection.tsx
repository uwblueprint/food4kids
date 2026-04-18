import { useState } from 'react';

import girlConfused from '@/assets/illustrations/girl-confused.png';
import {
  AlertCell,
  type Column,
  DataTable,
  DropdownTable,
  type DropdownTableRow,
} from '@/common/components';

import { SectionHeader } from '../components/SectionHeader';
import { SpecNote } from '../components/SpecNote';

// ---------------------------------------------------------------------------
// DropdownTable mock data
// ---------------------------------------------------------------------------

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

// ---------------------------------------------------------------------------
// DataTable mock data
// ---------------------------------------------------------------------------

type AlertType = 'error' | 'warning';

interface MockRow {
  id: number;
  alertType: AlertType;
  alert: string;
  rowNum: number;
  name: string;
  address: string;
  deliveryGroup: string;
  phone: string;
  errorCell?: 'address' | 'deliveryGroup';
}

const MOCK_ROWS: MockRow[] = [
  {
    id: 1,
    alertType: 'error',
    alert: 'Missing Address',
    rowNum: 12,
    name: 'Smith',
    address: '',
    deliveryGroup: 'Monday A',
    phone: '416 123 4850',
    errorCell: 'address',
  },
  {
    id: 2,
    alertType: 'error',
    alert: 'Missing Address',
    rowNum: 43,
    name: 'Connor',
    address: '',
    deliveryGroup: 'Tuesday A',
    phone: '416 343 8450',
    errorCell: 'address',
  },
  {
    id: 3,
    alertType: 'error',
    alert: 'Missing Address',
    rowNum: 45,
    name: 'Dougall',
    address: '',
    deliveryGroup: 'Thursday B',
    phone: '416 233 8450',
    errorCell: 'address',
  },
  {
    id: 4,
    alertType: 'error',
    alert: 'Missing Address',
    rowNum: 51,
    name: 'Morales',
    address: '',
    deliveryGroup: 'Tuesday A',
    phone: '519 343 8450',
    errorCell: 'address',
  },
  {
    id: 5,
    alertType: 'warning',
    alert: 'Duplicate Entry',
    rowNum: 78,
    name: 'Patel',
    address: '400 Oak Ave',
    deliveryGroup: 'Monday A',
    phone: '427 284 2498',
  },
  {
    id: 6,
    alertType: 'warning',
    alert: 'Duplicate Entry',
    rowNum: 89,
    name: 'Patel',
    address: '400 Oak Ave',
    deliveryGroup: 'Monday A',
    phone: '427 284 2498',
  },
  {
    id: 7,
    alertType: 'warning',
    alert: 'Missing Delivery Day',
    rowNum: 120,
    name: 'Jordan',
    address: '43 Burr Ave',
    deliveryGroup: '',
    phone: '519 5443 298',
    errorCell: 'deliveryGroup',
  },
];

const DATA_COLUMNS: Column<MockRow>[] = [
  {
    key: 'alert',
    header: 'Alert',
    render: (row) => <AlertCell type={row.alertType} label={row.alert} />,
  },
  { key: 'rowNum', header: 'Row' },
  { key: 'name', header: 'School / Last Name' },
  {
    key: 'address',
    header: 'Address',
    getCellClassName: (row) =>
      row.errorCell === 'address'
        ? 'bg-light-red border-b-2 border-red'
        : undefined,
  },
  {
    key: 'deliveryGroup',
    header: 'Delivery Group',
    getCellClassName: (row) =>
      row.errorCell === 'deliveryGroup'
        ? 'bg-light-yellow border-b-2 border-dark-yellow'
        : undefined,
  },
  { key: 'phone', header: 'Phone Number' },
];

const emptyState = (
  <div className="flex flex-col items-center justify-center gap-3 py-16 text-center">
    <img src={girlConfused} alt="" className="h-28 w-auto" />
    <div>
      <p className="text-p2 text-grey-500 font-medium">
        No new entries found in the spreadsheet
      </p>
      <p className="text-p3 text-grey-400">It's feeling quite empty here</p>
    </div>
  </div>
);

// ---------------------------------------------------------------------------
// Section
// ---------------------------------------------------------------------------

export function TableSection() {
  const [values, setValues] = useState<Record<number, string>>({});

  const dropdownRows: DropdownTableRow[] = INITIAL_ROWS.map((row, i) => ({
    ...row,
    value: values[i],
    onValueChange: (v) => setValues((prev) => ({ ...prev, [i]: v })),
  }));

  return (
    <section className="mb-16">
      <SectionHeader>Tables</SectionHeader>

      <div className="space-y-12">
        <div className="space-y-4">
          <SpecNote title="Dropdown Table">
            Two-column mapping table — pairs system column labels with a
            user-selectable file column dropdown.
          </SpecNote>
          <DropdownTable rows={dropdownRows} />
        </div>

        <div className="space-y-4">
          <SpecNote title="Data Table">
            Tabular data display with support for custom cell rendering,
            per-cell error/warning states via getCellClassName, and an empty
            state slot.
          </SpecNote>
          <DataTable
            columns={DATA_COLUMNS}
            rows={MOCK_ROWS}
            getRowKey={(row) => row.id}
            emptyState={emptyState}
          />
          <DataTable
            columns={DATA_COLUMNS}
            rows={[]}
            getRowKey={(row) => row.id}
            emptyState={emptyState}
          />
        </div>
      </div>
    </section>
  );
}
