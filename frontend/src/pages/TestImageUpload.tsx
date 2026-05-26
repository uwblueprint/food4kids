import { type ChangeEvent, useEffect, useRef, useState } from 'react';

import { Input } from '@/common/components/Input';

const API_BASE = 'http://localhost:8080';

export const TestImageUpload = () => {
  const [status, setStatus] = useState<
    'idle' | 'uploading' | 'success' | 'error'
  >('idle');
  const [result, setResult] = useState<{
    url: string;
    filename: string;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    return () => {
      if (preview) {
        URL.revokeObjectURL(preview);
      }
    };
  }, [preview]);

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setResult(null);
    setError(null);
    setStatus('idle');
    setPreview(URL.createObjectURL(file));
  };

  const handleUpload = async () => {
    const file = inputRef.current?.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    setStatus('uploading');
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/upload/`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Upload failed');
      }

      const data = await response.json();
      setResult(data);
      setStatus('success');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
      setStatus('error');
    }
  };

  const handleDelete = async () => {
    if (!result?.filename) return;

    try {
      const response = await fetch(`${API_BASE}/upload/${result.filename}`, {
        method: 'DELETE',
      });

      if (!response.ok) throw new Error('Delete failed');

      setResult(null);
      setPreview(null);
      setStatus('idle');
      if (inputRef.current) inputRef.current.value = '';
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Delete failed');
    }
  };

  return (
    <div className="mx-auto max-w-md space-y-4 p-6">
      <div className="space-y-2">
        <label
          htmlFor="picture"
          className="block text-sm font-medium text-gray-700"
        >
          Picture
        </label>
        <Input
          ref={inputRef}
          id="picture"
          type="file"
          accept="image/png,image/jpeg,image/gif,application/pdf"
          onChange={handleFileChange}
          className="text-sm file:mr-4 file:rounded file:bg-blue-50 file:px-4 file:py-2 file:font-semibold file:text-blue-700 hover:file:bg-blue-100"
        />
        <p className="text-sm text-gray-500">
          Select a picture to upload (max 5MB).
        </p>
      </div>

      {preview && (
        <img
          src={preview}
          alt="Preview"
          className="max-h-48 w-full rounded-lg object-cover"
        />
      )}

      <button
        onClick={handleUpload}
        disabled={status === 'uploading' || !preview}
        className="w-full rounded-lg bg-blue-600 px-4 py-2 text-white transition hover:bg-blue-700 disabled:opacity-50"
      >
        {status === 'uploading' ? 'Uploading...' : 'Upload'}
      </button>

      {status === 'success' && result && (
        <div className="space-y-2 rounded-lg bg-green-50 p-4">
          <p className="text-sm font-medium text-green-700">
            ✓ Uploaded successfully
          </p>
          <p className="text-xs break-all text-gray-500">
            Filename: {result.filename}
          </p>
          <button
            onClick={handleDelete}
            className="w-full rounded bg-red-100 px-3 py-1 text-sm text-red-600 transition hover:bg-red-200"
          >
            Delete
          </button>
        </div>
      )}

      {status === 'error' && error && (
        <p className="text-sm text-red-600">✗ {error}</p>
      )}
    </div>
  );
};
