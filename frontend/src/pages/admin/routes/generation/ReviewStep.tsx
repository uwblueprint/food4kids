import { useState } from 'react';
import { Link, useNavigate, useOutletContext } from 'react-router-dom';

import CheckIcon from '@/assets/icons/check.svg?react';
import XIcon from '@/assets/icons/x.svg?react';
import type { Column } from '@/common/components';
import {
  Button,
  DataTable,
  Modal,
  ModalContent,
  ModalDescription,
  ModalFooter,
  ModalHeader,
  ModalTitle,
  Tag,
} from '@/common/components';
import type {
  ChangedEntry,
  ChangedField,
  NetNewEntry,
  StaleEntry,
} from '@/types/location';

import { EmptyState } from '../components';
import type { GenerationOutletContext } from './AdminRoutesGenerationLayout';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function isChanged<T>(v: T | ChangedField<T>): v is ChangedField<T> {
  return (
    typeof v === 'object' &&
    v !== null &&
    'new_value' in (v as object) &&
    'old_value' in (v as object)
  );
}

function ChangedCell({
  value,
}: {
  value:
    | string
    | null
    | ChangedField<string | null>
    | ChangedField<number | null>
    | number
    | null;
}) {
  if (!isChanged(value)) {
    return <span>{value ?? '—'}</span>;
  }
  return (
    <div className="flex flex-col gap-1">
      <span className="bg-success-fill text-success-stroke inline-block rounded px-2 py-0.5 text-xs font-medium">
        {value.new_value ?? '—'}
      </span>
      <span className="bg-light-red text-red border-red inline-block rounded-t border-b-2 px-2 py-0.5 text-xs font-medium">
        {value.old_value ?? '—'}
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Column definitions
// ---------------------------------------------------------------------------

const netNewColumns: Column<NetNewEntry>[] = [
  { key: 'row', header: 'Row', render: (r) => String(r.row) },
  {
    key: 'contact_name',
    header: 'School / Last Name',
    render: (r) => r.contact_name,
  },
  { key: 'address', header: 'Address', render: (r) => r.address },
  {
    key: 'delivery_group',
    header: 'Delivery Group',
    render: (r) => r.delivery_group ?? '—',
  },
  {
    key: 'phone_number',
    header: 'Phone Number',
    render: (r) => r.phone_number,
  },
];

const staleColumns: Column<StaleEntry>[] = [
  {
    key: 'contact_name',
    header: 'School / Last Name',
    render: (r) => r.contact_name,
  },
  { key: 'address', header: 'Address', render: (r) => r.address },
  {
    key: 'delivery_group',
    header: 'Delivery Group',
    render: (r) => r.delivery_group ?? '—',
  },
  {
    key: 'phone_number',
    header: 'Phone Number',
    render: (r) => r.phone_number,
  },
];

// ---------------------------------------------------------------------------
// ReviewStep
// ---------------------------------------------------------------------------

// TODO: replace with real data from POST /locations/review once endpoint is implemented
const PLACEHOLDER_NET_NEW: NetNewEntry[] = [];
const PLACEHOLDER_STALE: StaleEntry[] = [];
const PLACEHOLDER_CHANGED: ChangedEntry[] = [];

export function ReviewStep() {
  const navigate = useNavigate();
  useOutletContext<GenerationOutletContext>(); // ensures we're inside the layout

  const [accepted, setAccepted] = useState<Set<number>>(new Set());
  const [confirmOpen, setConfirmOpen] = useState(false);

  const toggleAccepted = (index: number) => {
    setAccepted((prev) => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  };

  const handleConfirm = () => {
    setConfirmOpen(false);
    navigate('/admin/routes/generation/configure');
  };

  const changedColumns: Column<ChangedEntry & { _index: number }>[] = [
    {
      key: 'contact_name',
      header: 'School / Last Name',
      render: (r) => r.contact_name,
    },
    {
      key: 'address',
      header: 'Address',
      render: (r) => <ChangedCell value={r.address} />,
    },
    {
      key: 'delivery_group',
      header: 'Delivery Group',
      render: (r) => <ChangedCell value={r.delivery_group} />,
    },
    {
      key: 'phone_number',
      header: 'Phone Number',
      render: (r) => <ChangedCell value={r.phone_number} />,
    },
    {
      key: 'num_children',
      header: 'Number of Children',
      render: (r) => <ChangedCell value={r.num_children} />,
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (r) => {
        const isAccepted = accepted.has(r._index);
        return (
          <div className="flex items-center gap-2">
            <Button
              variant="primary"
              shape="circular"
              aria-label="Accept new value"
              onClick={() => !isAccepted && toggleAccepted(r._index)}
              className={isAccepted ? 'opacity-100' : 'opacity-40'}
            >
              <CheckIcon className="size-4" />
            </Button>
            <Button
              variant="secondary"
              shape="circular"
              aria-label="Keep old value"
              onClick={() => isAccepted && toggleAccepted(r._index)}
            >
              <XIcon className="size-4" />
            </Button>
          </div>
        );
      },
    },
  ];

  const changedRows = PLACEHOLDER_CHANGED.map((entry, i) => ({
    ...entry,
    _index: i,
  }));

  return (
    <>
      {/* New in Spreadsheet */}
      <section className="flex flex-col gap-3">
        <div>
          <h2 className="text-grey-500">New in Spreadsheet</h2>
          <p className="text-p1 text-grey-400">
            New entries to be added to the system.
          </p>
        </div>
        <DataTable
          columns={netNewColumns}
          rows={PLACEHOLDER_NET_NEW}
          getRowKey={(r) => r.row}
          emptyState={
            <EmptyState
              title="No new entries found in the spreadsheet"
              description="It's feeling quite empty here"
            />
          }
        />
      </section>

      {/* Removed in Spreadsheet */}
      <section className="flex flex-col gap-3">
        <div>
          <h2 className="text-grey-500">Removed in Spreadsheet</h2>
          <p className="text-p1 text-grey-400">
            Entries to be archived in the system.
          </p>
        </div>
        <DataTable
          columns={staleColumns}
          rows={PLACEHOLDER_STALE}
          getRowKey={(r) => r.location_id}
          emptyState={
            <EmptyState
              title="No new entries found in the spreadsheet"
              description="It's feeling quite empty here"
            />
          }
        />
      </section>

      {/* Data that has Changed */}
      <section className="flex flex-col gap-3">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-grey-500">Data that has Changed</h2>
            <p className="text-p1 text-grey-400">
              Entries that have data that was changed from previous upload.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Tag variant="success">New</Tag>
            <Tag variant="error">Old</Tag>
          </div>
        </div>
        <DataTable
          columns={changedColumns}
          rows={changedRows}
          getRowKey={(r) => r._index}
          emptyState={
            <EmptyState
              title="No new entries found in the spreadsheet"
              description="It's feeling quite empty here"
            />
          }
        />
      </section>

      {/* Actions */}
      <div className="flex items-center justify-between">
        <Button variant="tertiary" asChild>
          <Link to="/admin/routes/generation/validate">Back to Validation</Link>
        </Button>
        <Button variant="primary" onClick={() => setConfirmOpen(true)}>
          Continue to Configure Routes
        </Button>
      </div>

      {/* Confirmation Changes Modal */}
      <Modal open={confirmOpen} onOpenChange={setConfirmOpen}>
        <ModalContent>
          <ModalHeader>
            <ModalTitle>Confirm Changes</ModalTitle>
            <ModalDescription>
              Some data has been updated, added, or removed. Are you sure you
              want to apply these changes?
            </ModalDescription>
          </ModalHeader>
          <ModalFooter>
            <Button variant="secondary" onClick={() => setConfirmOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleConfirm}>
              Apply Changes
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  );
}
