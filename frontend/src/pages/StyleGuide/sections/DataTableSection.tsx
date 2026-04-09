import girlConfused from '@/assets/illustrations/girl-confused.png';
import { AlertCell, DataTable, type Column } from '@/common/components';

import { SectionHeader } from '../components/SectionHeader';

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

const COLUMNS: Column<MockRow>[] = [
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

export function DataTableSection() {
  return (
    <section className="mb-16">
      <SectionHeader>Data Table</SectionHeader>

      <div className="space-y-8">
        <DataTable
          columns={COLUMNS}
          rows={MOCK_ROWS}
          getRowKey={(row) => row.id}
          emptyState={emptyState}
        />

        <DataTable
          columns={COLUMNS}
          rows={[]}
          getRowKey={(row) => row.id}
          emptyState={emptyState}
        />
      </div>
    </section>
  );
}
