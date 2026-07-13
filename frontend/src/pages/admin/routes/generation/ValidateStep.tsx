import { useMemo, useState } from 'react';
import {
  Link,
  Navigate,
  useNavigate,
  useOutletContext,
} from 'react-router-dom';

import type {
  AlertCode,
  DuplicateMatchField,
  LocationImportResponse,
  LocationImportRow,
} from '@/api/generated/types.gen';
import type { Column } from '@/common/components';
import { AlertCell, Banner, Button, DataTable } from '@/common/components';

import { EmptyState } from '../components';
import type { GenerationOutletContext } from './AdminRoutesGenerationLayout';

// Styling for error cells — all alerts are blocking and use the same red error.
const ERROR_CELL_CLASS = 'border-b-2 border-red bg-light-red';

// ---------------------------------------------------------------------------
// Alert display helpers
// ---------------------------------------------------------------------------

function getAlertDisplay(code: AlertCode): {
  type: 'error' | 'warning';
  label: string;
} {
  switch (code) {
    case 'MISSING_NAME':
      return { type: 'error', label: 'Missing Name' };
    case 'INVALID_NAME':
      return { type: 'error', label: 'Invalid Name' };
    case 'MISSING_ADDRESS':
      return { type: 'error', label: 'Missing Address' };
    case 'INVALID_ADDRESS':
      return { type: 'error', label: 'Invalid Address' };
    case 'MISSING_PHONE_NUMBER':
      return { type: 'error', label: 'Missing Phone Number' };
    case 'INVALID_PHONE_NUMBER':
      return { type: 'error', label: 'Invalid Phone Number' };
    case 'MISSING_DELIVERY_GROUP':
      return { type: 'error', label: 'Missing Delivery Group' };
    case 'LOCAL_DUPLICATE':
      return { type: 'error', label: 'Duplicate Entry' };
    default: {
      const _exhaustive: never = code;
      return { type: 'error', label: _exhaustive };
    }
  }
}

const hasContactNameAlert = (alerts: AlertCode[]) =>
  alerts.includes('MISSING_NAME') || alerts.includes('INVALID_NAME');

const hasAddressAlert = (alerts: AlertCode[]) =>
  alerts.includes('MISSING_ADDRESS') || alerts.includes('INVALID_ADDRESS');

const hasPhoneAlert = (alerts: AlertCode[]) =>
  alerts.includes('MISSING_PHONE_NUMBER') ||
  alerts.includes('INVALID_PHONE_NUMBER');

// Returns the cell highlight class for non-alert data columns
function getCellClass(
  hasFieldError: boolean,
  duplicateField?: DuplicateMatchField,
  duplicateFields?: Set<DuplicateMatchField>
): string | undefined {
  if (
    hasFieldError ||
    (duplicateField !== undefined && duplicateFields?.has(duplicateField))
  ) {
    return ERROR_CELL_CLASS;
  }
  return undefined;
}

export function ValidateStep() {
  const navigate = useNavigate();
  const { file, reviewResult } = useOutletContext<GenerationOutletContext>();
  const duplicateFieldsByRow = useMemo(() => {
    const byRow = new Map<number, Set<DuplicateMatchField>>();
    for (const group of reviewResult?.duplicate_groups ?? []) {
      for (const row of group.rows) {
        const fields = byRow.get(row) ?? new Set<DuplicateMatchField>();
        for (const field of group.matching_fields) {
          fields.add(field);
        }
        byRow.set(row, fields);
      }
    }
    return byRow;
  }, [reviewResult?.duplicate_groups]);

  // Track which data the user dismissed the banner for. The banner is shown
  // again automatically when a new response comes in (different reference).
  const [dismissedFor, setDismissedFor] = useState<
    LocationImportResponse | undefined
  >(undefined);

  // Review runs on the Import step; without a result there's nothing to show.
  if (!file || !reviewResult) {
    return <Navigate to="/admin/routes/generation/import" replace />;
  }

  const data = reviewResult;
  const bannerDismissed = dismissedFor === data;
  const errorRows = data.rows.filter((r) => r.alerts.length > 0);
  const errorCount = errorRows.length;
  const canContinue = data.success === true;

  const handleContinue = () => {
    navigate('/admin/routes/generation/review');
  };

  const columns: Column<LocationImportRow>[] = [
    {
      key: 'alerts',
      header: 'Alert',
      render: (row) => {
        if (row.alerts.length === 0) return null;
        return (
          <AlertCell
            type="error"
            label={row.alerts.map((code) => getAlertDisplay(code).label)}
          />
        );
      },
    },
    {
      key: 'row',
      header: 'Row',
      render: (row) => String(row.row),
      getCellClassName: () => getCellClass(false),
    },
    {
      key: 'contact_name',
      header: 'School / Last Name',
      render: (row) => row.location.contact_name ?? '',
      getCellClassName: (row) =>
        getCellClass(
          hasContactNameAlert(row.alerts),
          'contact_name',
          duplicateFieldsByRow.get(row.row)
        ),
    },
    {
      key: 'address',
      header: 'Address',
      render: (row) => row.location.address ?? '',
      getCellClassName: (row) =>
        getCellClass(
          hasAddressAlert(row.alerts),
          'address',
          duplicateFieldsByRow.get(row.row)
        ),
    },
    {
      key: 'delivery_group',
      header: 'Delivery Group',
      render: (row) => row.location.delivery_group ?? '',
      getCellClassName: (row) =>
        getCellClass(
          row.alerts.includes('MISSING_DELIVERY_GROUP') &&
            !row.location.delivery_group
        ),
    },
    {
      key: 'phone_primary',
      header: 'Primary Phone',
      render: (row) => row.location.phone_primary ?? '',
      getCellClassName: (row) =>
        getCellClass(
          hasPhoneAlert(row.alerts),
          'phone_primary',
          duplicateFieldsByRow.get(row.row)
        ),
    },
  ];

  return (
    <>
      {/* Error banner */}
      {!bannerDismissed && !data.success && (
        <Banner variant="error" onDismiss={() => setDismissedFor(data)}>
          Please correct these{' '}
          <span className="text-red font-bold">{errorCount}</span>{' '}
          {errorCount === 1 ? 'error' : 'errors'} before continuing, then go
          back to import to reupload the file.
        </Banner>
      )}

      {/* Success banner */}
      {!bannerDismissed && data.success && (
        <Banner variant="success" onDismiss={() => setDismissedFor(data)}>
          No errors. You may proceed to the next step.
        </Banner>
      )}

      {/* Validation card */}
      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-1">
          <h2 className="text-grey-500">Validation</h2>
          <p className="text-p1 text-grey-500">
            Below are all the records from your imported file with alerts to
            resolve
          </p>
        </div>
        <DataTable
          columns={columns}
          rows={errorRows}
          getRowKey={(row) => row.row}
          emptyState={
            <EmptyState
              title="No new entries found in the spreadsheet"
              description="It's feeling quite empty here"
            />
          }
        />
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between">
        <Button variant="tertiary" asChild>
          <Link to="/admin/routes/generation/import">Back to Import</Link>
        </Button>
        <Button
          variant="primary"
          disabled={!canContinue}
          onClick={handleContinue}
        >
          Continue to Review
        </Button>
      </div>
    </>
  );
}
