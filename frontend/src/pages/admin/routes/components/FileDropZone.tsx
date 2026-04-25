import { useRef, useState } from 'react';

import ShareIcon from '@/assets/icons/share.svg?react';
import { cn } from '@/lib/utils';

interface FileDropZoneProps {
  onFileSelect: (file: File) => void;
  accept?: string;
  disabled?: boolean;
  className?: string;
}

function FileDropZone({
  onFileSelect,
  accept = '.xlsx',
  disabled,
  className,
}: FileDropZoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFiles = (files: FileList | null) => {
    if (!files || files.length === 0) return;
    onFileSelect(files[0]);
  };

  return (
    <div
      role="button"
      tabIndex={disabled ? -1 : 0}
      aria-label="Upload file"
      className={cn(
        'flex h-[248px] cursor-pointer flex-col items-center justify-center gap-4',
        'border-spacing-8 rounded-2xl border border-dashed border-blue-100',
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
        <p className="font-nunito text-h2 font-bold">
          <span className="text-blue-300">Click to upload</span>{' '}
          <span className="text-grey-500">or drag and drop</span>
        </p>
        <p className="text-p1 text-grey-500">
          <span className="text-red">* </span>
          Excel files (.xlsx) only
        </p>
      </div>
    </div>
  );
}

export { FileDropZone };
