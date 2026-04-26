import { type ReactNode } from 'react';

import AlertCircle from '@/assets/icons/alert-circle.svg?react';
import AlertTriangle from '@/assets/icons/alert-triangle.svg?react';
import { cn } from '@/lib/utils';

export interface Column<T> {
  key: string;
  header: string;
  /** Custom cell renderer. Falls back to `row[key]` as a string. */
  render?: (row: T) => ReactNode;
  /** Per-cell className based on row data — use for error/warning cell states. */
  getCellClassName?: (row: T) => string | undefined;
  /** Static className applied to the header <th> cell. */
  headerClassName?: string;
}

export interface DataTableProps<T> {
  columns: Column<T>[];
  rows: T[];
  getRowKey: (row: T) => string | number;
  /** Per-row className based on row data — use for error/warning row states. */
  getRowClassName?: (row: T) => string | undefined;
  /** Rendered when rows is empty. */
  emptyState?: ReactNode;
  className?: string;
}

// ---------------------------------------------------------------------------
// AlertCell — use inside a column's render() for the alert column pattern
// ---------------------------------------------------------------------------

interface AlertCellProps {
  type: 'error' | 'warning';
  label: string;
}

function AlertCell({ type, label }: AlertCellProps) {
  const isError = type === 'error';
  return (
    <span
      className={cn(
        'flex items-center gap-1.5',
        isError ? 'text-red' : 'text-dark-yellow'
      )}
    >
      {isError ? (
        <AlertCircle className="h-4 w-4 shrink-0" />
      ) : (
        <AlertTriangle className="h-4 w-4 shrink-0" />
      )}
      <span className="text-p2 font-medium">{label}</span>
    </span>
  );
}

// ---------------------------------------------------------------------------
// DataTable
// ---------------------------------------------------------------------------

function DataTable<T>({
  columns,
  rows,
  getRowKey,
  getRowClassName,
  emptyState,
  className,
}: DataTableProps<T>) {
  return (
    <div
      className={cn(
        'border-grey-300 overflow-hidden rounded-2xl border bg-white',
        className
      )}
    >
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-grey-300 border-b">
              {columns.map((col) => (
                <th
                  key={col.key}
                  className={cn('text-p2 px-6 py-4 text-left font-semibold whitespace-nowrap', col.headerClassName)}
                >
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>

          <tbody className="divide-grey-300 divide-y">
            {rows.length === 0 ? (
              <tr>
                <td colSpan={columns.length}>{emptyState}</td>
              </tr>
            ) : (
              rows.map((row) => (
                <tr key={getRowKey(row)} className={getRowClassName?.(row)}>
                  {columns.map((col) => (
                    <td
                      key={col.key}
                      className={cn(
                        'text-p2 text-grey-500 px-6 py-4 whitespace-nowrap',
                        col.getCellClassName?.(row)
                      )}
                    >
                      {col.render
                        ? col.render(row)
                        : String(
                            (row as Record<string, unknown>)[col.key] ?? ''
                          )}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export { AlertCell, DataTable };
