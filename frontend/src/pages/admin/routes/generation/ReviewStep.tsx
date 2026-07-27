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
type ChangedRow = ChangedEntry & { _index: number };

function isChanged<T>(v: T | ChangedField<T>): v is ChangedField<T> {
  return (
    typeof v === 'object' &&
    v !== null &&
    'new_value' in (v as object) &&
    'old_value' in (v as object)
  );
}

function newValue<T>(value: T | ChangedField<T>): T {
  return isChanged(value) ? value.new_value : value;
}

function oldValue<T>(value: T | ChangedField<T>): T {
  return isChanged(value) ? value.old_value : value;
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
    halal: entry.halal,
    dietary_restrictions: entry.dietary_restrictions,
  };
}

function changedEntryToNetNew(
  entry: ChangedEntry
): ValidatedLocationImportEntry {
  return {
    contact_name: entry.contact_name,
    address: newValue(entry.address),
    delivery_group: newValue(entry.delivery_group) ?? '',
    phone_primary: newValue(entry.phone_primary),
    phone_secondary: newValue(entry.phone_secondary),
    num_children: newValue(entry.num_children),
    halal: entry.halal,
    dietary_restrictions: entry.dietary_restrictions,
  };
}

function changedEntryToStale(entry: ChangedEntry): StaleEntry {
  return {
    location_id: entry.location_id,
    contact_name: entry.contact_name,
    address: oldValue(entry.address),
    delivery_group: oldValue(entry.delivery_group),
    phone_primary: oldValue(entry.phone_primary),
    phone_secondary: oldValue(entry.phone_secondary),
  };
}

export function ReviewStep() {
  const navigate = useNavigate();
  const { file, reviewResult, selectedDeliveryType } =
    useOutletContext<GenerationOutletContext>();
  const { mutateAsync: ingestLocations, isPending: isIngesting } =
    useIngestLocations();

  const [changedDecisions, setChangedDecisions] = useState<
    Map<number, 'apply' | 'separate'>
  >(new Map());
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [ingestError, setIngestError] = useState<string | null>(null);

  if (!file || !reviewResult || !selectedDeliveryType) {
    return <Navigate to="/admin/routes/generation/import" replace />;
  }

  const data = reviewResult;
  const netNewRows = data.net_new ?? [];
  const staleRows = data.stale ?? [];
  const changedEntries = data.changed ?? [];

  const setChangedDecision = (
    index: number,
    decision: 'apply' | 'separate'
  ) => {
    setChangedDecisions((prev) => {
      const next = new Map(prev);
      next.set(index, decision);
      return next;
    });
  };

  const handleConfirm = async () => {
    setIngestError(null);
    const approvedChanged = changedEntries.filter(
      (_, index) => changedDecisions.get(index) === 'apply'
    );
    const separateChanged = changedEntries.filter(
      (_, index) => changedDecisions.get(index) === 'separate'
    );

    try {
      await ingestLocations({
        delivery_type: selectedDeliveryType,
        net_new: [
          ...netNewRows.map(toIngestNetNew),
          ...separateChanged.map(changedEntryToNetNew),
        ],
        stale: [...staleRows, ...separateChanged.map(changedEntryToStale)],
        changed: approvedChanged,
      });
      setConfirmOpen(false);
      navigate('/admin/routes/generation/configure');
    } catch {
      setIngestError('Could not apply the import changes — please try again.');
    }
  };

  const changedColumns: Column<ChangedRow>[] = [
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
      header: 'Decision',
      render: (r) => {
        const decision = changedDecisions.get(r._index);
        return (
          <div className="flex items-center gap-2">
            <Button
              variant="primary"
              shape="circular"
              aria-label="Apply this change"
              title="Apply change"
              aria-pressed={decision === 'apply'}
              onClick={() => setChangedDecision(r._index, 'apply')}
              className={decision === 'apply' ? 'opacity-100' : 'opacity-40'}
            >
              <CheckIcon className="size-4" />
            </Button>
            <Button
              variant="secondary"
              shape="circular"
              aria-label="Treat as separate rows"
              title="Treat as separate rows"
              aria-pressed={decision === 'separate'}
              onClick={() => setChangedDecision(r._index, 'separate')}
              className={decision === 'separate' ? 'opacity-100' : 'opacity-40'}
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
  const appliedChangedCount = [...changedDecisions.values()].filter(
    (decision) => decision === 'apply'
  ).length;
  const separateChangedCount = [...changedDecisions.values()].filter(
    (decision) => decision === 'separate'
  ).length;
  const allChangesDecided = changedDecisions.size === changedEntries.length;

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
            Entries to be marked inactive in the system.
          </p>
        </div>
        <DataTable
          columns={staleColumns}
          rows={staleRows}
          getRowKey={(r) => r.location_id}
          emptyState={
            <EmptyState
              title="No removed entries found in the spreadsheet"
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
              Select whether each matched row is a change or a separate
              location.
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
        <Button
          variant="primary"
          disabled={!allChangesDecided}
          onClick={() => setConfirmOpen(true)}
        >
          Continue to Configure Routes
        </Button>
      </div>

      {/* Confirmation Changes Modal */}
      <Modal open={confirmOpen} onOpenChange={setConfirmOpen}>
        <ModalContent>
          <ModalHeader>
            <ModalTitle>Confirm Changes</ModalTitle>
            <ModalDescription>
              This will add {netNewRows.length + separateChangedCount} new{' '}
              {netNewRows.length + separateChangedCount === 1
                ? 'location'
                : 'locations'}
              , mark {staleRows.length + separateChangedCount}{' '}
              {staleRows.length + separateChangedCount === 1
                ? 'location'
                : 'locations'}{' '}
              inactive, and apply {appliedChangedCount}{' '}
              {appliedChangedCount === 1 ? 'matched change' : 'matched changes'}
              .
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
