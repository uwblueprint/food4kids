import { useEffect, useState } from 'react';
import { Link, useNavigate, useOutletContext } from 'react-router-dom';
import girlConfused from '@/assets/illustrations/girl-confused.png';

import { useValidateLocations } from '@/api';
import {
  AlertCell,
  Banner,
  Button,
  Card,
  DataTable,
} from '@/common/components';
import type { Column } from '@/common/components';
import type { AlertCode, LocationImportRow } from '@/types/location';

import type { GenerationOutletContext } from './AdminRoutesGenerationLayout';

// ---------------------------------------------------------------------------
// Alert display helpers
// ---------------------------------------------------------------------------

function getAlertDisplay(
  code: AlertCode,
  location: LocationImportRow['location']
): { type: 'error' | 'warning'; label: string } {
  switch (code) {
    case 'MISSING_FIELDS': {
      const missing: string[] = [];
      if (!location.contact_name) missing.push('Name');
      if (!location.address) missing.push('Address');
      if (!location.phone_number) missing.push('Phone');
      const label =
        missing.length === 1 ? `Missing ${missing[0]}` : 'Missing Fields';
      return { type: 'error', label };
    }
    case 'INVALID_FORMAT':
      return { type: 'error', label: 'Invalid Format' };
    case 'LOCAL_DUPLICATE':
      return { type: 'error', label: 'Duplicate Entry' };
    case 'PARTIAL_DUPLICATE':
      return { type: 'warning', label: 'Duplicate Entry' };
    case 'MISSING_DELIVERY_GROUP':
      return { type: 'warning', label: 'Missing Delivery Group' };
  }
}

const MISSING_CELL_CLASS = 'border-b-2 border-red bg-red-50';

// ---------------------------------------------------------------------------
// Empty state
// ---------------------------------------------------------------------------
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
// ValidateStep
// ---------------------------------------------------------------------------

export function ValidateStep() {
  const navigate = useNavigate();
  const { file, columnMap } = useOutletContext<GenerationOutletContext>();
  const { mutate, data, isPending, isError } = useValidateLocations();
  const [bannerDismissed, setBannerDismissed] = useState(false);

  // Redirect back if no file in context (e.g. page refresh)
  useEffect(() => {
    if (!file) {
      navigate('/admin/routes/generation/import', { replace: true });
      return;
    }
    mutate({ file, columnMap });
  }, []);

  // Reset banner when new results come in
  useEffect(() => {
    setBannerDismissed(false);
  }, [data]);

  const errorRows = data?.rows.filter((r) => r.alerts.length > 0) ?? [];
  const errorCount = errorRows.length;
  const canContinue = data?.success === true;

  const columns: Column<LocationImportRow>[] = [
    {
      key: 'alerts',
      header: 'Alert',
      render: (row) => {
        const first = row.alerts[0];
        if (!first) return null;
        const { type, label } = getAlertDisplay(first, row.location);
        return <AlertCell type={type} label={label} />;
      },
    },
    {
      key: 'row',
      header: 'Row',
      render: (row) => String(row.row),
    },
    {
      key: 'contact_name',
      header: 'School / Last Name',
      render: (row) => row.location.contact_name ?? '',
      getCellClassName: (row) =>
        row.alerts.includes('MISSING_FIELDS') && !row.location.contact_name
          ? MISSING_CELL_CLASS
          : undefined,
    },
    {
      key: 'address',
      header: 'Address',
      render: (row) => row.location.address ?? '',
      getCellClassName: (row) =>
        row.alerts.includes('MISSING_FIELDS') && !row.location.address
          ? MISSING_CELL_CLASS
          : undefined,
    },
    {
      key: 'delivery_group',
      header: 'Delivery Group',
      render: (row) => row.location.delivery_group ?? '',
      getCellClassName: (row) =>
        row.alerts.includes('MISSING_DELIVERY_GROUP') &&
        !row.location.delivery_group
          ? MISSING_CELL_CLASS
          : undefined,
    },
    {
      key: 'phone_number',
      header: 'Phone Number',
      render: (row) => row.location.phone_number ?? '',
      getCellClassName: (row) =>
        row.alerts.includes('MISSING_FIELDS') && !row.location.phone_number
          ? MISSING_CELL_CLASS
          : undefined,
    },
  ];

  return (
    <>
      {/* Error banner */}
      {!bannerDismissed && data && !data.success && (
        <Banner variant="error" onDismiss={() => setBannerDismissed(true)}>
          Please correct these <span className="font-bold">{errorCount}</span>{' '}
          {errorCount === 1 ? 'error' : 'errors'} before continuing, then go
          back to import to reupload the file.
        </Banner>
      )}

      {/* Success banner */}
      {!bannerDismissed && data && data.success && (
        <Banner variant="success" onDismiss={() => setBannerDismissed(true)}>
          No errors. You may proceed to the next step.
        </Banner>
      )}

      {/* Validation card */}
      <Card className="flex flex-col gap-4 p-6">
        <div className="flex flex-col gap-1">
          <h2 className="text-grey-500">Validation</h2>
          <p className="text-p1 text-grey-500">
            Below are all the records from your imported file with alerts to
            resolve
          </p>
        </div>

        {isPending && (
          <p className="text-p1 text-grey-400 py-8 text-center">Validating…</p>
        )}

        {isError && (
          <p className="text-p1 text-red py-8 text-center">
            Validation failed — please try again.
          </p>
        )}

        {data && (
          <DataTable
            columns={columns}
            rows={errorRows}
            getRowKey={(row) => row.row}
            getRowClassName={(row) =>
              row.alerts.includes('PARTIAL_DUPLICATE')
                ? 'bg-yellow-50'
                : undefined
            }
            emptyState={emptyState}
          />
        )}
      </Card>

      {/* Actions */}
      <div className="flex items-center justify-between">
        <Button variant="tertiary" asChild>
          <Link to="/admin/routes/generation/import">Back to Import</Link>
        </Button>
        <Button variant="primary" disabled={!canContinue}>
          Continue to Review
        </Button>
      </div>
    </>
  );
}
