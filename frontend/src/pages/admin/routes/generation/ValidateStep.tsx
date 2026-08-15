import { useMemo } from 'react';
import {
  Link,
  Navigate,
  useNavigate,
  useOutletContext,
} from 'react-router-dom';

import type {
  AlertCode,
  DuplicateMatchField,
  LocationImportRow,
} from '@/api/generated/types.gen';
import type { Column } from '@/common/components';
import { AlertCell, Button, DataTable } from '@/common/components';
import { formatPhone } from '@/common/utils';

import { EmptyState } from '../components';
import type { GenerationOutletContext } from './AdminRoutesGenerationLayout';
import { GenerationFooter } from './GenerationFooter';

// Styling for error cells — all alerts are blocking and use the same red error.
const ERROR_CELL_CLASS = 'border-b border-red bg-light-red';

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
    case 'INVALID_SECONDARY_PHONE_NUMBER':
      return { type: 'error', label: 'Invalid Secondary Phone Number' };
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

const hasSecondaryPhoneAlert = (alerts: AlertCode[]) =>
  alerts.includes('INVALID_SECONDARY_PHONE_NUMBER');

const hasInvalidOrMissingAlert = (row: { alerts: AlertCode[] }) =>
  row.alerts.some((code) => code !== 'LOCAL_DUPLICATE');

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

  // Review runs on the Import step; without a result there's nothing to show.
  if (!file || !reviewResult) {
    return <Navigate to="/admin/routes/generation/import" replace />;
  }

  const data = reviewResult;
  const errorRows = data.rows.filter((r) => r.alerts.length > 0);
  const canContinue = data.success === true;

  // The frames split validation into two tables because the two problems have
  // different remedies. A row can land in both — a duplicate that is also
  // missing a delivery group needs fixing twice — and each table shows only
  // the alerts it is responsible for.
  const invalidRows = errorRows.filter((r) => hasInvalidOrMissingAlert(r));
  const duplicateRows = errorRows.filter((r) =>
    r.alerts.includes('LOCAL_DUPLICATE')
  );

  const handleContinue = () => {
    navigate('/admin/routes/generation/review');
  };

  const alertColumn = (
    scope: 'invalid' | 'duplicate'
  ): Column<LocationImportRow> => ({
    key: 'alerts',
    header: 'Error',
    render: (row) => {
      const codes = row.alerts.filter((code) =>
        scope === 'duplicate'
          ? code === 'LOCAL_DUPLICATE'
          : code !== 'LOCAL_DUPLICATE'
      );
      if (codes.length === 0) return null;
      return (
        <AlertCell
          type="error"
          label={codes.map((code) => getAlertDisplay(code).label)}
        />
      );
    },
  });

  // Each table highlights only the cells it is about: the invalid/missing
  // table marks the fields that failed validation, the duplicate table marks
  // the fields that matched another row. A row in both tables therefore shows
  // a different set of red cells in each.
  const dataColumns = (
    scope: 'invalid' | 'duplicate'
  ): Column<LocationImportRow>[] => {
    const invalid = scope === 'invalid';
    const duplicateFields = (row: LocationImportRow) =>
      invalid ? undefined : duplicateFieldsByRow.get(row.row);

    return [
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
          getCellClass(
            invalid && hasContactNameAlert(row.alerts),
            'contact_name',
            duplicateFields(row)
          ),
      },
      {
        key: 'address',
        header: 'Address',
        render: (row) => row.location.address ?? '',
        getCellClassName: (row) =>
          getCellClass(
            invalid && hasAddressAlert(row.alerts),
            'address',
            duplicateFields(row)
          ),
      },
      {
        key: 'delivery_group',
        header: 'Delivery Group',
        render: (row) => row.location.delivery_group ?? '',
        getCellClassName: (row) =>
          getCellClass(
            invalid &&
              row.alerts.includes('MISSING_DELIVERY_GROUP') &&
              !row.location.delivery_group
          ),
      },
      {
        key: 'phone_primary',
        header: 'Phone Number',
        // Valid numbers were normalized during validation, so this shows the
        // stored form; an invalid one keeps the admin's raw text (formatPhone
        // passes it through) so they can see what to fix.
        render: (row) =>
          row.location.phone_primary
            ? formatPhone(row.location.phone_primary)
            : '',
        getCellClassName: (row) =>
          getCellClass(
            invalid && hasPhoneAlert(row.alerts),
            'phone_primary',
            duplicateFields(row)
          ),
      },
      // INVALID_SECONDARY_PHONE_NUMBER is a blocking alert, so the value has
      // to be on screen — otherwise the admin is told to fix something they
      // cannot see. Never a duplicate field: the 2-of-3 rule uses the primary.
      {
        key: 'phone_secondary',
        header: 'Secondary Phone Number',
        render: (row) =>
          row.location.phone_secondary
            ? formatPhone(row.location.phone_secondary)
            : '',
        getCellClassName: (row) =>
          getCellClass(invalid && hasSecondaryPhoneAlert(row.alerts)),
      },
    ];
  };

  return (
    <>
      <section className="flex flex-col gap-4">
        <div className="flex flex-col gap-1">
          <h2 className="text-grey-500">Invalid / Missing Entries</h2>
          <p className="text-p1 text-grey-500">
            Resolve all errors, then go back to Import to upload a new file
          </p>
        </div>
        <DataTable
          columns={[alertColumn('invalid'), ...dataColumns('invalid')]}
          rows={invalidRows}
          getRowKey={(row) => row.row}
          emptyState={
            <EmptyState
              compact
              image="girl-searching"
              title="No entries found"
              description="No action required at this time"
            />
          }
        />
      </section>

      <section className="flex flex-col gap-4">
        <div className="flex flex-col gap-1">
          <h2 className="text-grey-500">Duplicate Entries</h2>
          <p className="text-p1 text-grey-500">
            Correct all duplicate entries, then go back to Import to upload a
            new file
          </p>
        </div>
        <DataTable
          columns={[alertColumn('duplicate'), ...dataColumns('duplicate')]}
          rows={duplicateRows}
          getRowKey={(row) => row.row}
          emptyState={
            <EmptyState
              compact
              image="girl-searching"
              title="No entries found"
              description="No action required at this time"
            />
          }
        />
      </section>

      <GenerationFooter>
        <Button variant="tertiary" asChild>
          <Link to="/admin/routes/generation/import">Back to import</Link>
        </Button>
        <Button
          variant="primary"
          disabled={!canContinue}
          onClick={handleContinue}
        >
          Continue to review changes
        </Button>
      </GenerationFooter>
    </>
  );
}
