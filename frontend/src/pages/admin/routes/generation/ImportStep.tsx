import { useState } from 'react';
import { Link, useNavigate, useOutletContext } from 'react-router-dom';
import * as XLSX from 'xlsx';

import {
  getConfiguredDeliveryTypes,
  usePreviewLocationImport,
  useSystemSettings,
} from '@/api';
import type { Column } from '@/common/components';
import {
  Banner,
  Button,
  DataTable,
  Dropdown,
  DropdownContent,
  DropdownItem,
  DropdownTrigger,
  DropdownValue,
  FileInput,
} from '@/common/components';

import type { GenerationOutletContext } from './AdminRoutesGenerationLayout';
import { GenerationFooter } from './GenerationFooter';

const ACCEPTED_EXTENSIONS = new Set(['.xlsx']);

// Radix Select cannot hold an item whose value is the empty string, so the
// "leave unmapped" choice an optional field needs carries a sentinel that is
// translated back to '' before it reaches the column map.
const UNMAPPED = '__unmapped__';

interface SystemField {
  key: string;
  label: string;
  required?: boolean;
}

const SYSTEM_FIELDS: SystemField[] = [
  { key: 'contact_name', label: 'School Name / Last Name', required: true },
  { key: 'guardian_name', label: 'Guardian Name', required: true },
  { key: 'address', label: 'Address', required: true },
  { key: 'delivery_group', label: 'Delivery Group', required: true },
  { key: 'phone_primary', label: 'Phone Number', required: true },
  // Optional to match the backend: `phone_secondary` is a ChangedFieldOptStr
  // and is absent from `_has_required_fields`, so a roster without a second
  // phone column still imports. It is only validated when non-empty.
  { key: 'phone_secondary', label: 'Secondary Phone Number' },
  { key: 'num_children', label: 'Number of Children', required: true },
  { key: 'dietary_restrictions', label: 'Food Restrictions', required: true },
  { key: 'halal', label: 'Halal?', required: true },
];

// Parses headers from uploaded Excel file
function parseHeaders(file: File): Promise<string[]> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = e.target?.result;
        const workbook = XLSX.read(data, { type: 'array' });
        const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
        const rows = XLSX.utils.sheet_to_json<string[]>(firstSheet, {
          header: 1,
        });
        const headers = (rows[0] ?? []).map(String).filter(Boolean);
        resolve(headers);
      } catch {
        reject(new Error('Could not parse file headers'));
      }
    };
    reader.onerror = () => reject(new Error('Could not read file'));
    reader.readAsArrayBuffer(file);
  });
}

export function ImportStep() {
  const navigate = useNavigate();
  const {
    file,
    setFile,
    fileHeaders,
    setFileHeaders,
    columnMap,
    setColumnMap,
    selectedDeliveryType,
    setSelectedDeliveryType,
    setReviewResult,
  } = useOutletContext<GenerationOutletContext>();

  const { mutateAsync: previewImport, isPending: isReviewing } =
    usePreviewLocationImport();
  const { data: systemSettings } = useSystemSettings();
  const deliveryTypes = getConfiguredDeliveryTypes(systemSettings);

  const [formatError, setFormatError] = useState<string | null>(null);
  const [reviewError, setReviewError] = useState<string | null>(null);

  const handleFileSelect = async (selected: File) => {
    const ext = '.' + selected.name.split('.').pop()?.toLowerCase();
    if (!ACCEPTED_EXTENSIONS.has(ext)) {
      setFormatError(
        'Unsupported format. Please upload an Excel (.xlsx) file.'
      );
      return;
    }
    setFormatError(null);
    try {
      const headers = await parseHeaders(selected);
      setFile(selected);
      setFileHeaders(headers);
      setReviewResult(null);
      // Drop any saved mappings whose target column isn't in this file
      const validHeaders = new Set(headers);
      setColumnMap(
        Object.fromEntries(
          Object.entries(columnMap).filter(([, val]) => validHeaders.has(val))
        )
      );
    } catch {
      setFormatError('Could not read file headers — is the file valid?');
    }
  };

  const handleClearFile = () => {
    setFile(null);
    setFileHeaders([]);
    setReviewResult(null);
  };

  const headerOptions = fileHeaders.map((h) => ({ label: h, value: h }));

  const columns: Column<SystemField>[] = [
    {
      key: 'label',
      header: 'System Column',
      // 56px rows — the frames give this table more air than the others
      // because every row holds a control. The header is 48 and top-aligned:
      // the frames draw it as a 40px box with 16px of air beneath, which a
      // borderless table row can only approximate, and this is the split that
      // lands both the header text and every row on their frame y.
      headerClassName: 'h-12 align-top',
      getCellClassName: () => 'h-14',
      render: (row) => (
        // P1, not the table's usual P2 — these are field labels rather than
        // imported data, and the frames set them 16/500.
        <span className="text-p1 text-grey-500">
          {row.label}
          {row.required && <span className="text-red">{' *'}</span>}
        </span>
      ),
    },
    {
      key: 'value',
      header: 'Your File Column',
      headerClassName: 'h-12 align-top',
      getCellClassName: () => 'h-14',
      render: (row) => (
        <Dropdown
          value={columnMap[row.key] ?? ''}
          onValueChange={(val) =>
            setColumnMap({
              ...columnMap,
              [row.key]: val === UNMAPPED ? '' : val,
            })
          }
        >
          <DropdownTrigger>
            <DropdownValue placeholder="Select Column" />
          </DropdownTrigger>
          <DropdownContent>
            {/* An optional field has to be un-settable again: without this the
                first pick would be permanent for the rest of the wizard. */}
            {!row.required && (
              <DropdownItem value={UNMAPPED}>Not in my file</DropdownItem>
            )}
            {headerOptions.map((opt) => (
              <DropdownItem key={opt.value} value={opt.value}>
                {opt.label}
              </DropdownItem>
            ))}
          </DropdownContent>
        </Dropdown>
      ),
    },
  ];

  const canContinue =
    selectedDeliveryType !== '' &&
    file !== null &&
    SYSTEM_FIELDS.filter((f) => f.required).every((f) => !!columnMap[f.key]);

  const handleContinue = async () => {
    if (!file || !selectedDeliveryType) return;
    setReviewError(null);
    try {
      const result = await previewImport({
        file,
        columnMap,
        deliveryType: selectedDeliveryType,
      });
      setReviewResult(result);
      // A clean preview leaves the validate step with nothing to show and
      // nothing to fix, so go straight to review.
      navigate(
        result.success
          ? '/admin/routes/generation/review'
          : '/admin/routes/generation/validate'
      );
    } catch {
      setReviewError('Could not validate the file — please try again.');
    }
  };

  return (
    <>
      {reviewError && (
        <Banner variant="error" onDismiss={() => setReviewError(null)}>
          {reviewError}
        </Banner>
      )}

      <section className="flex flex-col gap-4">
        <div className="flex flex-col gap-1">
          <h2 className="text-grey-500">Select Delivery Type</h2>
          <p className="text-p1 text-grey-500">
            Choose the type of spreadsheet you'll be uploading:
          </p>
        </div>
        {/* 28px pitch: a 24px-tall row per the frames, 4px apart. */}
        <div className="flex flex-col gap-1">
          {deliveryTypes.map((deliveryType) => (
            <label
              key={deliveryType}
              className="text-p1 flex cursor-pointer items-center gap-2"
            >
              <input
                type="radio"
                name="delivery-type"
                value={deliveryType}
                checked={selectedDeliveryType === deliveryType}
                onChange={() => {
                  setSelectedDeliveryType(deliveryType);
                  setFile(null);
                  setFileHeaders([]);
                  setReviewResult(null);
                  setFormatError(null);
                }}
                className="size-5 cursor-pointer accent-blue-300"
              />
              {deliveryType}
            </label>
          ))}
        </div>
      </section>

      {selectedDeliveryType && (
        <section className="flex max-w-[700px] flex-col gap-4">
          <div className="flex flex-col gap-1">
            <h2 className="text-grey-500">Import Data</h2>
            <p className="text-p1 text-grey-500">
              Upload an Excel file (.xlsx) with delivery information
            </p>
          </div>
          <div className="flex flex-col gap-4">
            <FileInput
              onFileSelect={handleFileSelect}
              selectedFile={file}
              onClearFile={handleClearFile}
              accept=".xlsx"
              acceptedFileTypesLabel="Excel files (.xlsx) only"
            />
            {formatError && (
              <Banner
                variant="error"
                className="items-center p-4"
                onDismiss={() => setFormatError(null)}
              >
                {formatError}
              </Banner>
            )}
          </div>
        </section>
      )}

      {/* Map Columns Table */}
      {file && (
        <div className="flex flex-col gap-4">
          <div className="flex flex-col gap-1">
            <h2 className="text-grey-500">Map Columns</h2>
            <p className="text-p1 text-grey-500">
              Match columns in your file to the fields in our database
            </p>
          </div>
          <DataTable
            columns={columns}
            rows={SYSTEM_FIELDS}
            getRowKey={(row) => row.key}
          />
          {/* 8px under the card, not the section's 16. */}
          <p className="text-p2 text-grey-400 -mt-2 text-right font-semibold">
            Columns can be customized from the{' '}
            <Link to="/admin/settings" className="text-blue-300">
              Settings
            </Link>{' '}
            page
          </p>
        </div>
      )}

      <GenerationFooter>
        <Button variant="tertiary" asChild>
          <Link to="/admin/routes">Back to routes</Link>
        </Button>
        <Button
          variant="primary"
          disabled={!canContinue || isReviewing}
          onClick={handleContinue}
        >
          {isReviewing ? 'Validating…' : 'Continue to validate'}
        </Button>
      </GenerationFooter>
    </>
  );
}
