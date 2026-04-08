import { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import ShareIcon from '@/assets/icons/share.svg?react';
import XIcon from '@/assets/icons/x.svg?react';
import { Badge, Banner, Button, Dropdown } from '@/common/components';
import { cn } from '@/lib/utils';

const SYSTEM_COLUMNS = [
  'School Name / Child Last Name',
  'Address',
  'Delivery Group',
  'Phone Number',
  'Number of Children',
  'Food Restrictions',
];

export const ImportStep = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDraggingOver, setIsDraggingOver] = useState(false);
  const [hasFormatError, setHasFormatError] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);

  const handleFile = (file: File) => {
    if (!file.name.endsWith('.xlsx')) {
      setHasFormatError(true);
      return;
    }
    setHasFormatError(false);
    setUploadedFile(file);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
    e.target.value = '';
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDraggingOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleFile(file);
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDraggingOver(true);
  };

  const handleDragLeave = () => setIsDraggingOver(false);

  const handleRemoveFile = (e: React.MouseEvent) => {
    e.stopPropagation();
    setUploadedFile(null);
  };

  return (
    <div className="flex flex-col gap-6">
      {hasFormatError && (
        <Banner variant="error">
          Unsupported format — please upload an Excel (.xlsx) file
        </Banner>
      )}

      {/* Upload card */}
      <div className="border-grey-300 flex flex-col gap-4 rounded-2xl border bg-white p-6">
        <div className="flex flex-col gap-1">
          <h2>Import Data</h2>
          <p className="text-p1 text-grey-400">
            Upload an Excel file (.xlsx) with delivery information
          </p>
        </div>

        <div
          className={cn(
            'flex cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed py-12 transition-colors',
            isDraggingOver
              ? 'border-blue-300 bg-blue-50'
              : 'border-grey-300 bg-white'
          )}
          onClick={() => fileInputRef.current?.click()}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
        >
          <ShareIcon className="text-grey-400 size-10" />
          <div className="text-center">
            <p className="text-p1">
              <span className="font-semibold text-blue-300">
                Click to upload
              </span>{' '}
              or drag and drop
            </p>
            <p className="text-p2 text-grey-400">
              <span className="text-red">*</span>Excel files (.xlsx) only
            </p>
          </div>

          {uploadedFile && (
            <Badge
              variant="success"
              className="cursor-default"
              onClick={(e) => e.stopPropagation()}
            >
              {uploadedFile.name}
              <button
                onClick={handleRemoveFile}
                aria-label="Remove file"
                className="hover:opacity-70"
              >
                <XIcon className="size-3.5" />
              </button>
            </Badge>
          )}
        </div>

        <input
          ref={fileInputRef}
          type="file"
          accept=".xlsx"
          className="hidden"
          onChange={handleFileChange}
        />
      </div>

      {/* Map Columns — only shown after file is uploaded */}
      {uploadedFile && (
        <div className="flex flex-col gap-3">
          <div className="flex flex-col gap-1">
            <h2>Map Columns</h2>
            <p className="text-p1 text-grey-400">
              Tell the system which columns in your file match our required data
              fields. Mapping will be saved for future uploads.
            </p>
          </div>

          <div className="border-grey-300 rounded-2xl border bg-white">
            <div className="border-grey-300 grid grid-cols-2 border-b px-6 py-3">
              <p className="text-p2 font-semibold">System Column</p>
              <p className="text-p2 font-semibold">Your File Column</p>
            </div>

            <div className="divide-grey-300 divide-y">
              {SYSTEM_COLUMNS.map((col) => (
                <div
                  key={col}
                  className="grid grid-cols-2 items-center gap-4 px-6 py-4"
                >
                  <p className="text-p2">
                    {col}
                    <span className="text-red">*</span>
                  </p>
                  <Dropdown
                    placeholder="Select Column"
                    options={[]}
                    // TODO: wire up value/onValueChange with column mapping state
                  />
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Bottom nav */}
      <div className="flex justify-between">
        <Button
          variant="tertiary"
          className="w-auto"
          onClick={() => navigate('/routes/generation')}
        >
          Back to Route Options
        </Button>
        <Button
          className="w-auto"
          disabled={!uploadedFile}
          onClick={() => navigate('../validate')}
        >
          Continue to Validation
        </Button>
      </div>
    </div>
  );
};
