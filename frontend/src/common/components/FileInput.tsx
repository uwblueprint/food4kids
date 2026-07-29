import { useRef, useState } from 'react';

import ShareIcon from '@/assets/icons/share.svg?react';
import XIcon from '@/assets/icons/x.svg?react';
import { cn } from '@/lib/utils';

interface FileInputProps {
  onFileSelect: (file: File) => void;
  selectedFile?: File | null;
  onClearFile?: () => void;
  accept?: string;
  acceptedFileTypesLabel?: string;
  disabled?: boolean;
  className?: string;
}

function FileInput({
  onFileSelect,
  selectedFile,
  onClearFile,
  accept = '.xlsx',
  acceptedFileTypesLabel = 'Excel files (.xlsx) only',
  disabled,
  className,
}: FileInputProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFiles = (files: FileList | null) => {
    if (!files || files.length === 0) return;
    onFileSelect(files[0]);
  };

  if (selectedFile) {
    const sizeInKb = selectedFile.size / 1024;
    const displaySize =
      sizeInKb >= 1024
        ? `${(sizeInKb / 1024).toFixed(2)} MB`
        : `${sizeInKb.toFixed(2)} KB`;

    return (
      <div
        className={cn(
          'border-grey-300 flex h-16 items-center rounded-lg border bg-white px-7',
          className
        )}
      >
        <div className="mr-4 flex size-9 shrink-0 items-center justify-center rounded bg-[#107c41] text-xs font-bold text-white">
          XLS
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-p1 truncate font-semibold">{selectedFile.name}</p>
          <p className="text-p2 text-grey-400">{displaySize}</p>
        </div>
        {onClearFile && (
          <button
            type="button"
            onClick={onClearFile}
            aria-label="Remove uploaded file"
            className="text-grey-500 hover:text-red ml-4 cursor-pointer"
          >
            <XIcon className="size-5" />
          </button>
        )}
      </div>
    );
  }

  return (
    <div
      role="button"
      tabIndex={disabled ? -1 : 0}
      aria-label="Upload file"
      className={cn(
        'flex h-[248px] cursor-pointer flex-col items-center justify-center gap-4',
        'rounded-2xl border border-dashed border-blue-100',
        'transition-colors',
        isDragging && 'bg-blue-50',
        disabled && 'pointer-events-none opacity-50',
        className
      )}
      onClick={() => inputRef.current?.click()}
      onKeyDown={(e) => e.key === 'Enter' && inputRef.current?.click()}
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setIsDragging(false);
        handleFiles(e.dataTransfer.files);
      }}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={(e) => handleFiles(e.target.files)}
      />
      <ShareIcon className="text-grey-400 size-11" />
      <div className="space-y-1 text-center">
        <p className="text-h2 font-bold">
          <span className="text-blue-300">Click to upload</span>{' '}
          <span className="text-grey-500">or drag and drop</span>
        </p>
        <p className="text-p1 text-grey-500">
          <span className="text-red">* </span>
          {acceptedFileTypesLabel}
        </p>
      </div>
    </div>
  );
}

export { FileInput };
