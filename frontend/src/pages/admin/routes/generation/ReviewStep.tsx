import { type ReactNode, useState } from 'react';
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

function DecisionButton({
  active,
  variant,
  label,
  onClick,
  children,
}: {
  active: boolean;
  variant: 'primary' | 'secondary';
  label: string;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <Button
      variant={variant}
      aria-label={label}
      onClick={onClick}
      className={active ? 'opacity-100' : 'opacity-45'}
    >
      {children}
    </Button>
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

  const [excludedNetNewRows, setExcludedNetNewRows] = useState<Set<number>>(
    new Set()
  );
  const [keptStaleIds, setKeptStaleIds] = useState<Set<string>>(new Set());
  const [separateChangedRows, setSeparateChangedRows] = useState<Set<number>>(
    new Set()
  );
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [ingestError, setIngestError] = useState<string | null>(null);

  if (!file || !reviewResult || !selectedDeliveryType) {
    return <Navigate to="/admin/routes/generation/import" replace />;
  }

  const data = reviewResult;
  const netNewRows = data.net_new ?? [];
  const staleRows = data.stale ?? [];
  const changedEntries = data.changed ?? [];

  const setNetNewIncluded = (row: number, included: boolean) => {
    setExcludedNetNewRows((prev) => {
      const next = new Set(prev);
      if (included) next.delete(row);
      else next.add(row);
      return next;
    });
  };

  const setStaleIncluded = (locationId: string, included: boolean) => {
    setKeptStaleIds((prev) => {
      const next = new Set(prev);
      if (included) next.delete(locationId);
      else next.add(locationId);
      return next;
    });
  };

  const setChangedSeparate = (index: number, separate: boolean) => {
    setSeparateChangedRows((prev) => {
      const next = new Set(prev);
      if (separate) next.add(index);
      else next.delete(index);
      return next;
    });
  };

  const handleConfirm = async () => {
    setIngestError(null);
    const approvedChanged = changedEntries.filter(
      (_, index) => !separateChangedRows.has(index)
    );
    const separateChanged = changedEntries.filter((_, index) =>
      separateChangedRows.has(index)
    );

    try {
      await ingestLocations({
        delivery_type: selectedDeliveryType,
        net_new: [
          ...netNewRows
            .filter((entry) => !excludedNetNewRows.has(entry.row))
            .map(toIngestNetNew),
          ...separateChanged.map(changedEntryToNetNew),
        ],
        stale: [
          ...staleRows.filter((entry) => !keptStaleIds.has(entry.location_id)),
          ...separateChanged.map(changedEntryToStale),
        ],
        changed: approvedChanged,
      });
      setConfirmOpen(false);
      navigate('/admin/routes/generation/configure');
    } catch {
      setIngestError('Could not apply the import changes — please try again.');
    }
  };

  const netNewReviewColumns: Column<NetNewEntry>[] = [
    ...netNewColumns,
    {
      key: 'decision',
      header: 'Decision',
      render: (r) => {
        const included = !excludedNetNewRows.has(r.row);
        return (
          <div className="flex items-center gap-2">
            <DecisionButton
              active={included}
              variant="primary"
              label="Add this row"
              onClick={() => setNetNewIncluded(r.row, true)}
            >
              Add
            </DecisionButton>
            <DecisionButton
              active={!included}
              variant="secondary"
              label="Skip this row"
              onClick={() => setNetNewIncluded(r.row, false)}
            >
              Skip
            </DecisionButton>
          </div>
        );
      },
    },
  ];

  const staleReviewColumns: Column<StaleEntry>[] = [
    ...staleColumns,
    {
      key: 'decision',
      header: 'Decision',
      render: (r) => {
        const included = !keptStaleIds.has(r.location_id);
        return (
          <div className="flex items-center gap-2">
            <DecisionButton
              active={included}
              variant="primary"
              label="Deactivate this location"
              onClick={() => setStaleIncluded(r.location_id, true)}
            >
              Deactivate
            </DecisionButton>
            <DecisionButton
              active={!included}
              variant="secondary"
              label="Keep this location active"
              onClick={() => setStaleIncluded(r.location_id, false)}
            >
              Keep
            </DecisionButton>
          </div>
        );
      },
    },
  ];

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
        const isSeparate = separateChangedRows.has(r._index);
        return (
          <div className="flex items-center gap-2">
            <Button
              variant="primary"
              aria-label="Apply this change"
              onClick={() => setChangedSeparate(r._index, false)}
              className={!isSeparate ? 'opacity-100' : 'opacity-45'}
            >
              <CheckIcon className="size-4" />
              Apply
            </Button>
            <Button
              variant="secondary"
              aria-label="Treat as separate rows"
              onClick={() => setChangedSeparate(r._index, true)}
              className={isSeparate ? 'opacity-100' : 'opacity-45'}
            >
              <XIcon className="size-4" />
              Separate
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
  const appliedNetNewCount = netNewRows.length - excludedNetNewRows.size;
  const appliedStaleCount = staleRows.length - keptStaleIds.size;
  const appliedChangedCount = changedEntries.length - separateChangedRows.size;
  const separateChangedCount = separateChangedRows.size;

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
            New rows can be added to the system or skipped for now.
          </p>
        </div>
        <DataTable
          columns={netNewReviewColumns}
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
            Removed locations can be marked inactive or kept as-is.
          </p>
        </div>
        <DataTable
          columns={staleReviewColumns}
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
              Apply a matched change, or treat the spreadsheet row as a separate
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
              This will add {appliedNetNewCount + separateChangedCount} new{' '}
              {appliedNetNewCount + separateChangedCount === 1
                ? 'location'
                : 'locations'}
              , mark {appliedStaleCount + separateChangedCount}{' '}
              {appliedStaleCount + separateChangedCount === 1
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
