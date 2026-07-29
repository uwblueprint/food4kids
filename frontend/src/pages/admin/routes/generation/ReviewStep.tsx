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
} from '@/common/components';
import { cn } from '@/lib/utils';

import { EmptyState } from '../components';
import type { GenerationOutletContext } from './AdminRoutesGenerationLayout';

type ChangedField<T> = { new_value: T; old_value: T };

function isChanged<T>(value: T | ChangedField<T>): value is ChangedField<T> {
  return (
    typeof value === 'object' &&
    value !== null &&
    'new_value' in (value as object) &&
    'old_value' in (value as object)
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

  // No vertical padding: `min-h-10` is border-box, so each half is exactly the
  // 40px the frames call for and a changed row totals 80.
  return (
    <div className="-mx-4 -my-2.5 flex flex-col">
      <span className="bg-grey-150 flex min-h-10 items-center gap-2 px-4">
        <span className="text-grey-400 text-base">−</span>
        {value.old_value ?? '—'}
      </span>
      <span className="flex min-h-10 items-center gap-2 border-b-2 border-blue-100 bg-blue-50 px-4">
        <span className="text-grey-400 text-base">+</span>
        {value.new_value ?? '—'}
      </span>
    </div>
  );
}

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

function ReviewStatus({
  reviewed,
  total,
}: {
  reviewed: number;
  total: number;
}) {
  const complete = reviewed === total && total > 0;

  return (
    <span
      className={cn(
        // Tag: 127×26, r40, 16px side padding, 14/600. Neutral until every row
        // in the section is checked off — 0 / 0 stays neutral.
        'inline-flex h-[26px] items-center rounded-full px-4 text-sm font-semibold',
        complete
          ? 'bg-success-fill text-success-stroke'
          : 'bg-grey-300 text-grey-500'
      )}
    >
      {reviewed} / {total} Reviewed
    </span>
  );
}

export function ReviewStep() {
  const navigate = useNavigate();
  const { file, reviewResult, selectedDeliveryType } =
    useOutletContext<GenerationOutletContext>();
  const { mutateAsync: ingestLocations, isPending: isIngesting } =
    useIngestLocations();

  const [reviewedChanged, setReviewedChanged] = useState<Set<number>>(
    new Set()
  );
  const [reviewedRemoved, setReviewedRemoved] = useState<Set<string>>(
    new Set()
  );
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [ingestError, setIngestError] = useState<string | null>(null);

  if (!file || !reviewResult || !selectedDeliveryType) {
    return <Navigate to="/admin/routes/generation/import" replace />;
  }

  const netNewRows = reviewResult.net_new ?? [];
  const staleRows = reviewResult.stale ?? [];
  const changedEntries = reviewResult.changed ?? [];

  const toggleChanged = (index: number) => {
    setReviewedChanged((previous) => {
      const next = new Set(previous);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  };

  const toggleRemoved = (locationId: string) => {
    setReviewedRemoved((previous) => {
      const next = new Set(previous);
      if (next.has(locationId)) {
        next.delete(locationId);
      } else {
        next.add(locationId);
      }
      return next;
    });
  };

  const allReviewed =
    reviewedChanged.size === changedEntries.length &&
    reviewedRemoved.size === staleRows.length;

  const handleConfirm = async () => {
    setIngestError(null);
    try {
      // Every change is applied. The checkboxes only attest that an admin has
      // looked at each row — they are not a per-row include/exclude.
      await ingestLocations({
        delivery_type: selectedDeliveryType,
        net_new: netNewRows.map(toIngestNetNew),
        stale: staleRows,
        changed: changedEntries,
      });
      setConfirmOpen(false);
      navigate('/admin/routes/generation/configure');
    } catch {
      // Close first: Radix marks the rest of the page aria-hidden and locks
      // body scroll while the modal is open, so a banner set behind it is
      // unreachable both visually and to screen readers.
      setConfirmOpen(false);
      setIngestError('Could not apply the import changes — please try again.');
    }
  };

  const changedColumns: Column<ChangedEntry & { _index: number }>[] = [
    {
      key: 'reviewed',
      header: '',
      headerClassName: 'w-8 px-2',
      render: (row) => (
        <input
          type="checkbox"
          checked={reviewedChanged.has(row._index)}
          onChange={() => toggleChanged(row._index)}
          aria-label={`Review changes for ${row.contact_name}`}
          className="border-grey-300 size-4 cursor-pointer rounded accent-blue-300"
        />
      ),
    },
    {
      key: 'contact_name',
      header: 'School / Last Name',
      render: (row) => row.contact_name,
    },
    {
      key: 'address',
      header: 'Address',
      render: (row) => <ChangedCell value={row.address} />,
    },
    {
      key: 'delivery_group',
      header: 'Delivery Group',
      render: (row) => <ChangedCell value={row.delivery_group} />,
    },
    {
      key: 'phone_primary',
      header: 'Phone Number',
      render: (row) => <ChangedCell value={row.phone_primary} />,
    },
    {
      key: 'num_children',
      header: 'Number of Children',
      render: (row) => <ChangedCell value={row.num_children} />,
    },
  ];

  const staleColumns: Column<StaleEntry>[] = [
    {
      key: 'reviewed',
      header: '',
      headerClassName: 'w-8 px-2',
      render: (row) => (
        <input
          type="checkbox"
          checked={reviewedRemoved.has(row.location_id)}
          onChange={() => toggleRemoved(row.location_id)}
          aria-label={`Review removal of ${row.contact_name}`}
          className="border-grey-300 size-4 cursor-pointer rounded accent-blue-300"
        />
      ),
    },
    {
      key: 'contact_name',
      header: 'School / Last Name',
      render: (row) => row.contact_name,
    },
    { key: 'address', header: 'Address', render: (row) => row.address },
    {
      key: 'delivery_group',
      header: 'Delivery Group',
      render: (row) => row.delivery_group ?? '—',
    },
    {
      key: 'phone_primary',
      header: 'Phone Number',
      render: (row) => row.phone_primary,
    },
    {
      key: 'num_children',
      header: 'Number of Children',
      render: () => '—',
    },
  ];

  const changedRows = changedEntries.map((entry, index) => ({
    ...entry,
    _index: index,
  }));

  return (
    <>
      {ingestError && (
        <Banner variant="error" onDismiss={() => setIngestError(null)}>
          {ingestError}
        </Banner>
      )}

      <section className="flex flex-col gap-4">
        <div className="flex items-end justify-between">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-grey-500">Changed Data</h2>
              <ReviewStatus
                reviewed={reviewedChanged.size}
                total={changedEntries.length}
              />
            </div>
            <p className="text-p1 text-grey-500">
              Check off entries that have changed since the previous upload to
              confirm you have reviewed them
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="border-grey-300 bg-grey-150 inline-flex h-[26px] items-center rounded-full border px-4 text-sm font-semibold">
              Old
            </span>
            <span className="inline-flex h-[26px] items-center rounded-full border border-blue-100 bg-blue-50 px-4 text-sm font-semibold">
              New
            </span>
          </div>
        </div>
        <DataTable
          columns={changedColumns}
          rows={changedRows}
          getRowKey={(row) => row._index}
          emptyState={
            <EmptyState
              compact
              title="No entries found"
              description="No action required at this time"
            />
          }
        />
      </section>

      <section className="flex flex-col gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-grey-500">Removed</h2>
            <ReviewStatus
              reviewed={reviewedRemoved.size}
              total={staleRows.length}
            />
          </div>
          <p className="text-p1 text-grey-500">
            Check off entries that were removed since the previous upload to
            confirm you have reviewed them
          </p>
        </div>
        <DataTable
          columns={staleColumns}
          rows={staleRows}
          getRowKey={(row) => row.location_id}
          emptyState={
            <EmptyState
              compact
              title="No entries found"
              description="No action required at this time"
            />
          }
        />
      </section>

      <div className="flex items-center justify-between">
        <Button variant="tertiary" asChild>
          <Link to="/admin/routes/generation/validate">Back to validate</Link>
        </Button>
        <Button
          variant="primary"
          disabled={!allReviewed}
          onClick={() => setConfirmOpen(true)}
        >
          Continue to edit route groups
        </Button>
      </div>

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
              {isIngesting ? 'Applying…' : 'Apply changes'}
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  );
}
