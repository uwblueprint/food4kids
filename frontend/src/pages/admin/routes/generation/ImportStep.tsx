import { useState } from 'react';
import { Link, useNavigate, useOutletContext } from 'react-router-dom';
import * as XLSX from 'xlsx';

import { useReviewLocations } from '@/api';
import type { Column } from '@/common/components';
import {
  Banner,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  DataTable,
  Dropdown,
  DropdownContent,
  DropdownItem,
  DropdownTrigger,
  DropdownValue,
  FileInput,
} from '@/common/components';

import type { GenerationOutletContext } from './AdminRoutesGenerationLayout';

const ACCEPTED_EXTENSIONS = new Set(['.xlsx']);

interface SystemField {
  key: string;
  label: string;
  required?: boolean;
}

const SYSTEM_FIELDS: SystemField[] = [
  { key: 'contact_name', label: 'School Name / Last Name', required: true },
  { key: 'address', label: 'Address', required: true },
  { key: 'delivery_group', label: 'Delivery Group', required: true },
  { key: 'phone_primary', label: 'Primary Phone', required: true },
  { key: 'phone_secondary', label: 'Secondary Phone' },
  { key: 'num_boxes', label: 'Number of Children', required: true },
  { key: 'dietary_restrictions', label: 'Food Restrictions' },
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
    setReviewResult,
  } = useOutletContext<GenerationOutletContext>();

  const { mutateAsync: reviewLocations, isPending: isReviewing } =
    useReviewLocations();

  const [formatError, setFormatError] = useState<string | null>(null);
  const [reviewError, setReviewError] = useState<string | null>(null);

  const handleFileSelect = async (selected: File) => {
    const ext = '.' + selected.name.split('.').pop()?.toLowerCase();
    if (!ACCEPTED_EXTENSIONS.has(ext)) {
      setFormatError(
        'Unsupported format — please upload an Excel (.xlsx) file'
      );
      return;
    }
    setFormatError(null);
    try {
      const headers = await parseHeaders(selected);
      setFile(selected);
      setFileHeaders(headers);
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
  };

  const headerOptions = fileHeaders.map((h) => ({ label: h, value: h }));

  const columns: Column<SystemField>[] = [
    {
      key: 'label',
      header: 'System Column',
      render: (row) => (
        <span className="text-p2 text-grey-500">
          {row.label}
          {row.required && <span className="text-red ml-0.5">*</span>}
        </span>
      ),
    },
    {
      key: 'value',
      header: 'Your File Column',
      render: (row) => (
        <Dropdown
          value={columnMap[row.key] ?? ''}
          onValueChange={(val) =>
            setColumnMap({ ...columnMap, [row.key]: val })
          }
        >
          <DropdownTrigger>
            <DropdownValue placeholder="Select Column" />
          </DropdownTrigger>
          <DropdownContent>
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
    file !== null &&
    SYSTEM_FIELDS.filter((f) => f.required).every((f) => !!columnMap[f.key]);

  const handleContinue = async () => {
    if (!file) return;
    setReviewError(null);
    try {
      const result = await reviewLocations({ file, columnMap });
      setReviewResult(result);
      navigate('/admin/routes/generation/validate');
    } catch {
      setReviewError('Could not validate the file — please try again.');
    }
  };

  return (
    <>
      {/* Error banner */}
      {formatError && (
        <Banner variant="error" onDismiss={() => setFormatError(null)}>
          {formatError}
        </Banner>
      )}
      {reviewError && (
        <Banner variant="error" onDismiss={() => setReviewError(null)}>
          {reviewError}
        </Banner>
      )}

      {/* Import Data Card */}
      <Card>
        <CardHeader>
          <CardTitle>Import Data</CardTitle>
          <CardDescription>
            Upload an Excel file (.xlsx) with delivery information
          </CardDescription>
        </CardHeader>
        <CardContent className="pt-4">
          <FileInput
            onFileSelect={handleFileSelect}
            selectedFile={file}
            onClearFile={handleClearFile}
          />
        </CardContent>
      </Card>

      {/* Map Columns Table */}
      {file && (
        <div className="flex flex-col gap-4">
          <div className="flex flex-col gap-1">
            <h2 className="text-grey-500">Map Columns</h2>
            <p className="text-p1 text-grey-500">
              Match your file's columns to the required system fields
            </p>
          </div>
          <DataTable
            columns={columns}
            rows={SYSTEM_FIELDS}
            getRowKey={(row) => row.key}
          />
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center justify-between">
        <Button variant="tertiary" asChild>
          <Link to="/admin/routes">Back to Routes</Link>
        </Button>
        <Button
          variant="primary"
          disabled={!canContinue || isReviewing}
          onClick={handleContinue}
        >
          {isReviewing ? 'Validating…' : 'Continue to Validation'}
        </Button>
      </div>
    </>
  );
}
