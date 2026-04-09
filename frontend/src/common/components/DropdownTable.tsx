import { cn } from '@/lib/utils';

import { Dropdown, type DropdownOption } from './Dropdown';

export interface DropdownTableRow {
  label: string;
  required?: boolean;
  options: DropdownOption[];
  value?: string;
  onValueChange?: (value: string) => void;
  placeholder?: string;
}

export interface DropdownTableProps {
  rows: DropdownTableRow[];
  systemColumnHeader?: string;
  fileColumnHeader?: string;
  className?: string;
}

function DropdownTable({
  rows,
  systemColumnHeader = 'System Column',
  fileColumnHeader = 'Your File Column',
  className,
}: DropdownTableProps) {
  return (
    <div
      className={cn(
        'border-grey-300 divide-grey-300 divide-y rounded-2xl border px-6 pt-4 pb-1',
        className
      )}
    >
      <div className="grid grid-cols-[2fr_3fr] pb-3">
        <span className="text-p2 font-semibold">{systemColumnHeader}</span>
        <span className="text-p2 font-semibold">{fileColumnHeader}</span>
      </div>

      {rows.map((row, i) => (
        <div
          key={i}
          className="grid grid-cols-[2fr_3fr] items-center gap-2 px-4 py-2.5"
        >
          <span className="text-p2 text-grey-500">
            {row.label}
            {row.required && <span className="text-red ml-0.5">*</span>}
          </span>
          <Dropdown
            options={row.options}
            value={row.value}
            onValueChange={row.onValueChange}
            placeholder={row.placeholder ?? 'Select Column'}
          />
        </div>
      ))}
    </div>
  );
}

export { DropdownTable };
