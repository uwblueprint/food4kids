import { useEffect, useState } from 'react';
import { Link, useNavigate, useOutletContext } from 'react-router-dom';
import * as XLSX from 'xlsx';

import { Banner, Button, Card, DropdownTable } from '@/common/components';
import type { DropdownTableRow } from '@/common/components';
import { FileDropZone } from '@/pages/admin/routes/components/FileDropZone';
import type { GenerationOutletContext } from './AdminRoutesGenerationLayout';

const ACCEPTED_EXTENSIONS = new Set(['.xlsx']);

const COLUMN_MAP_STORAGE_KEY = 'food4kids_column_map';

const SYSTEM_FIELDS: { key: string; label: string; required: boolean }[] = [
  { key: 'contact_name', label: 'School Name / Last Name', required: true },
  { key: 'address', label: 'Address', required: true },
  { key: 'delivery_group', label: 'Delivery Group', required: true },
  { key: 'phone_number', label: 'Phone Number', required: true },
  { key: 'num_boxes', label: 'Number of Children', required: true },
  { key: 'dietary_restrictions', label: 'Food Restrictions', required: true },
];

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

function loadSavedMapping(): Record<string, string> {
  try {
    const raw = localStorage.getItem(COLUMN_MAP_STORAGE_KEY);
    return raw ? (JSON.parse(raw) as Record<string, string>) : {};
  } catch {
    return {};
  }
}

export function ImportStep() {
  const navigate = useNavigate();
  const { file, setFile, columnMap, setColumnMap } =
    useOutletContext<GenerationOutletContext>();

  const [formatError, setFormatError] = useState<string | null>(null);
  const [fileHeaders, setFileHeaders] = useState<string[]>([]);

  // Restore saved mapping on mount
  useEffect(() => {
    const saved = loadSavedMapping();
    if (Object.keys(saved).length > 0) setColumnMap(saved);
  }, []);

  // If a file was already set in context (e.g. user navigated back), parse headers
  useEffect(() => {
    if (file && fileHeaders.length === 0) {
      parseHeaders(file)
        .then(setFileHeaders)
        .catch(() => {});
    }
  }, [file]);

  // Persist column map to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem(COLUMN_MAP_STORAGE_KEY, JSON.stringify(columnMap));
  }, [columnMap]);

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
    } catch {
      setFormatError('Could not read file headers — is the file valid?');
    }
  };

  const handleClearFile = () => {
    setFile(null);
    setFileHeaders([]);
  };

  const handleColumnChange = (systemKey: string, fileColumn: string) => {
    setColumnMap({ ...columnMap, [systemKey]: fileColumn });
  };

  const headerOptions = fileHeaders.map((h) => ({ label: h, value: h }));

  const dropdownRows: DropdownTableRow[] = SYSTEM_FIELDS.map((field) => ({
    label: field.label,
    required: field.required,
    options: headerOptions,
    value: columnMap[field.key] ?? '',
    onValueChange: (val) => handleColumnChange(field.key, val),
  }));

  const requiredFields = SYSTEM_FIELDS.filter((f) => f.required);
  const allRequiredMapped = requiredFields.every((f) => !!columnMap[f.key]);
  const canContinue = file !== null && allRequiredMapped;

  const handleContinue = () => {
    navigate('/admin/routes/generation/validate');
  };

  return (
    <>
      {/* Error banner */}
      {formatError && (
        <Banner variant="error" onDismiss={() => setFormatError(null)}>
          {formatError}
        </Banner>
      )}

      {/* Import card */}
      <Card className="flex flex-col gap-4 p-6">
        <div className="flex flex-col gap-1">
          <h2 className="text-grey-500">Import Data</h2>
          <p className="text-p1 text-grey-500">
            Upload an Excel file (.xlsx) with delivery information
          </p>
        </div>
        <FileDropZone
          onFileSelect={handleFileSelect}
          selectedFile={file}
          onClearFile={handleClearFile}
        />
      </Card>

      {/* Map Columns */}
      {file && (
        <div className="flex flex-col gap-4">
          <div className="flex flex-col gap-1">
            <h2 className="text-grey-500">Map Columns</h2>
            <p className="text-p1 text-grey-500">
              Match your file's columns to the required system fields
            </p>
          </div>
          <DropdownTable rows={dropdownRows} />
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center justify-between">
        <Button variant="tertiary" asChild>
          <Link to="/admin/routes">Back to Routes</Link>
        </Button>
        <Button
          variant="primary"
          disabled={!canContinue}
          onClick={canContinue ? handleContinue : undefined}
        >
          Continue to Validation
        </Button>
      </div>
    </>
  );
}
