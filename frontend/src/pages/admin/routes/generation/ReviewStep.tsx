import { useState } from 'react';
import {
  Link,
  Navigate,
  useNavigate,
  useOutletContext,
} from 'react-router-dom';

import { useIngestLocations } from '@/api';
import type {
  ChangedEntry,
  NetNewEntry,
  StaleEntry,
  ValidatedLocationImportEntry,
} from '@/api/generated/types.gen';
import CheckIcon from '@/assets/icons/check.svg?react';
import XIcon from '@/assets/icons/x.svg?react';
import type { Column } from '@/common/components';
import {
  Banner,
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

import { EmptyState } from '../components';
import type { GenerationOutletContext } from './AdminRoutesGenerationLayout';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * A field that either holds a plain value or a before/after change pair.
 * The generated client emits concrete variants (ChangedFieldStr, etc.); this
 * generic mirrors their shape for the isChanged guard and ChangedCell below.
 */
type ChangedField<T> = { new_value: T; old_value: T };

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
    | number
    | null
    | undefined
    | ChangedField<string | null>
    | ChangedField<number | null>;
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
    key: 'phone_primary',
    header: 'Primary Phone',
    render: (r) => r.phone_primary,
  },
  {
    key: 'phone_secondary',
    header: 'Secondary Phone',
    render: (r) => r.phone_secondary ?? '—',
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
    key: 'phone_primary',
    header: 'Primary Phone',
    render: (r) => r.phone_primary,
  },
  {
    key: 'phone_secondary',
    header: 'Secondary Phone',
    render: (r) => r.phone_secondary ?? '—',
  },
];

// ---------------------------------------------------------------------------
// ReviewStep
// ---------------------------------------------------------------------------

function toIngestNetNew(entry: NetNewEntry): ValidatedLocationImportEntry {
  return {
    contact_name: entry.contact_name,
    address: entry.address,
    delivery_group: entry.delivery_group ?? '',
    phone_primary: entry.phone_primary,
    phone_secondary: entry.phone_secondary,
    num_children: entry.num_children,
  };
}

export function ReviewStep() {
  const navigate = useNavigate();
  const { file, reviewResult, selectedDeliveryType } =
    useOutletContext<GenerationOutletContext>();
  const { mutateAsync: ingestLocations, isPending: isIngesting } =
    useIngestLocations();

  const [accepted, setAccepted] = useState<Set<number>>(new Set());
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [ingestError, setIngestError] = useState<string | null>(null);

  if (!file || !reviewResult || !selectedDeliveryType) {
    return <Navigate to="/admin/routes/generation/import" replace />;
  }

  const data = reviewResult;
  const netNewRows = data.net_new ?? [];
  const staleRows = data.stale ?? [];
  const changedEntries = data.changed ?? [];

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

  const handleConfirm = async () => {
    setIngestError(null);
    try {
      await ingestLocations({
        delivery_type: selectedDeliveryType,
        net_new: netNewRows.map(toIngestNetNew),
        stale: staleRows,
        changed: changedEntries,
      });
      setConfirmOpen(false);
      navigate('/admin/routes/generation/configure');
    } catch {
      setIngestError('Could not apply the import changes — please try again.');
    }
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
      key: 'phone_primary',
      header: 'Primary Phone',
      render: (r) => <ChangedCell value={r.phone_primary} />,
    },
    {
      key: 'phone_secondary',
      header: 'Secondary Phone',
      render: (r) => <ChangedCell value={r.phone_secondary} />,
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

  const changedRows = changedEntries.map((entry, i) => ({
    ...entry,
    _index: i,
  }));

  return (
    <>
      {ingestError && (
        <Banner variant="error" onDismiss={() => setIngestError(null)}>
          {ingestError}
        </Banner>
      )}

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
          rows={netNewRows}
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
          rows={staleRows}
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
            <Button
              variant="primary"
              disabled={isIngesting}
              onClick={handleConfirm}
            >
              {isIngesting ? 'Applying…' : 'Apply Changes'}
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  );
}
