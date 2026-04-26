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
        'border-grey-300 rounded-2xl border bg-white px-6 py-3',
        className
      )}
    >
      {/* Headers */}
      <div className="border-grey-300 mb-4 grid grid-cols-[2fr_3fr] border-b px-4 py-2.5">
        <span className="text-p2 font-semibold">{systemColumnHeader}</span>
        <span className="text-p2 font-semibold">{fileColumnHeader}</span>
      </div>

      <div className="flex flex-col gap-4">
        {rows.map((row, i) => (
          <div key={i} className="grid grid-cols-[2fr_3fr] items-center px-4">
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
    </div>
  );
}

export { DropdownTable };
