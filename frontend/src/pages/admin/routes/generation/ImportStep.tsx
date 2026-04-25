import { useState } from 'react';
import { Link } from 'react-router-dom';

import { Banner, Button, Card } from '@/common/components';

import { FileDropZone } from '@/pages/admin/routes/components/FileDropZone';

const ACCEPTED_EXTENSIONS = new Set(['.xlsx']);

export function ImportStep() {
  const [formatError, setFormatError] = useState<string | null>(null);

  const handleFileSelect = (file: File) => {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!ACCEPTED_EXTENSIONS.has(ext)) {
      setFormatError(
        'Unsupported format — please upload an Excel (.xlsx) file'
      );
      return;
    }
    setFormatError(null);
    // TODO: advance to /admin/routes/generate/validate with file state
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
        <FileDropZone onFileSelect={handleFileSelect} />
      </Card>

      {/* Back to Routes */}
      <Button variant="tertiary" className="self-start" asChild>
        <Link to="/admin/routes">Back to Routes</Link>
      </Button>
    </>
  );
}
