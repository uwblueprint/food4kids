import girlConfused from '@/assets/illustrations/girl-confused.png';
import { AlertCell, type Column, DataTable } from '@/common/components';

import { ComponentPreview } from '../components/ComponentPreview';
import { SectionDescription } from '../components/SectionDescription';
import { SectionHeader } from '../components/SectionHeader';
import { SectionLabel } from '../components/SectionLabel';
import { SpecNote } from '../components/SpecNote';

// ---------------------------------------------------------------------------
// Types & mock data
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
// Simple data for usage preview (no alerts or cell states)
// ---------------------------------------------------------------------------

interface SimpleRow {
  id: number;
  rowNum: number;
  name: string;
  address: string;
  deliveryGroup: string;
  phone: string;
}

const SIMPLE_ROWS: SimpleRow[] = [
  { id: 1, rowNum: 12, name: 'Smith', address: '14 Maple St', deliveryGroup: 'Monday A', phone: '416 123 4850' },
  { id: 2, rowNum: 43, name: 'Connor', address: '88 Birch Ave', deliveryGroup: 'Tuesday A', phone: '416 343 8450' },
  { id: 3, rowNum: 45, name: 'Dougall', address: '23 Cedar Rd', deliveryGroup: 'Thursday B', phone: '416 233 8450' },
  { id: 4, rowNum: 51, name: 'Morales', address: '7 Elm Cres', deliveryGroup: 'Tuesday A', phone: '519 343 8450' },
  { id: 5, rowNum: 78, name: 'Patel', address: '400 Oak Ave', deliveryGroup: 'Monday A', phone: '427 284 2498' },
];

const SIMPLE_COLUMNS: Column<SimpleRow>[] = [
  { key: 'rowNum', header: 'Row' },
  { key: 'name', header: 'School / Last Name' },
  { key: 'address', header: 'Address' },
  { key: 'deliveryGroup', header: 'Delivery Group' },
  { key: 'phone', header: 'Phone Number' },
];

// ---------------------------------------------------------------------------
// Code snippets
// ---------------------------------------------------------------------------

const DATA_TABLE_CODE = `import { type Column, DataTable } from '@/common/components';

interface Row {
  id: number;
  name: string;
  address: string;
  deliveryGroup: string;
  phone: string;
}

const columns: Column<Row>[] = [
  { key: 'name', header: 'School / Last Name' },
  { key: 'address', header: 'Address' },
  { key: 'deliveryGroup', header: 'Delivery Group' },
  { key: 'phone', header: 'Phone Number' },
];

<DataTable
  columns={columns}
  rows={rows}
  getRowKey={(row) => row.id}
  emptyState={<p>No rows found.</p>}
/>`;

// ---------------------------------------------------------------------------
// Section
// ---------------------------------------------------------------------------

export function TableSection() {
  return (
    <section className="mb-16">
      <SectionHeader>Tables</SectionHeader>
      <SectionDescription>
        Tabular data display built around{' '}
        <code className="text-p2 rounded bg-grey-150 px-1">DataTable</code>.
        Columns are defined as a typed array with optional custom cell renderers
        and per-cell error/warning highlight via{' '}
        <code className="text-p2 rounded bg-grey-150 px-1">
          getCellClassName
        </code>
        . Use{' '}
        <code className="text-p2 rounded bg-grey-150 px-1">AlertCell</code>{' '}
        inside a column's{' '}
        <code className="text-p2 rounded bg-grey-150 px-1">render</code> for
        inline error and warning indicators.
      </SectionDescription>

      <div className="mb-10 space-y-6">
        <SpecNote title="Column Definition">
          Each column requires a <code>key</code> (maps to a row field) and a{' '}
          <code>header</code> string. Provide a <code>render</code> function for
          custom cell content, or <code>getCellClassName</code> for conditional
          cell styling (e.g. error highlight).
        </SpecNote>
        <SpecNote title="Empty State">
          Pass any ReactNode to <code>emptyState</code> — shown when{' '}
          <code>rows</code> is empty.
        </SpecNote>
        <SpecNote title="AlertCell">
          Use <code>AlertCell</code> inside a column's render function to show
          error (red) or warning (yellow) icons with a label.
        </SpecNote>
      </div>

      <SectionLabel>Usage</SectionLabel>
      <div className="mb-8">
        <ComponentPreview
          title="Data Table"
          code={DATA_TABLE_CODE}
          previewClassName="block p-6"
        >
          <DataTable
            columns={SIMPLE_COLUMNS}
            rows={SIMPLE_ROWS}
            getRowKey={(row) => row.id}
          />
        </ComponentPreview>
      </div>

      <SectionLabel>States</SectionLabel>
      <div className="border-grey-300 bg-grey-150 overflow-hidden rounded-xl border p-6">
        <div className="space-y-8">
          <div>
            <p className="text-p3 mb-4 font-semibold tracking-wider text-blue-300 uppercase">
              With Data
            </p>
            <DataTable
              columns={DATA_COLUMNS}
              rows={MOCK_ROWS}
              getRowKey={(row) => row.id}
              emptyState={emptyState}
            />
          </div>
          <div>
            <p className="text-p3 mb-4 font-semibold tracking-wider text-blue-300 uppercase">
              Empty State
            </p>
            <DataTable
              columns={DATA_COLUMNS}
              rows={[]}
              getRowKey={(row) => row.id}
              emptyState={emptyState}
            />
          </div>
        </div>
      </div>
    </section>
  );
}
