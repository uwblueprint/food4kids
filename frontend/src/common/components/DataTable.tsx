import { type ReactNode, useMemo } from 'react';

import AlertCircle from '@/assets/icons/alert-circle.svg?react';
import AlertTriangle from '@/assets/icons/alert-triangle.svg?react';
import ChevronDown from '@/assets/icons/chevron-down.svg?react';
import ChevronUp from '@/assets/icons/chevron-up.svg?react';
import { cn } from '@/lib/utils';

/** Value a sortable column compares by. Nullish sorts to the end. */
type SortValue = string | number | Date | null | undefined;

export interface SortState {
  key: string;
  dir: 'asc' | 'desc';
}

export interface Column<T> {
  key: string;
  header: ReactNode;
  /** Custom cell renderer. Falls back to `row[key]` as a string. */
  render?: (row: T) => ReactNode;
  /** Per-cell className based on row data — use for error/warning cell states. */
  getCellClassName?: (row: T) => string | undefined;
  /** Static className applied to the header <th> cell. */
  headerClassName?: string;
  /** When set, the header is a sort toggle and rows sort by `sortValue`. */
  sortable?: boolean;
  /** Comparable value for sorting; required for the sort to do anything. */
  sortValue?: (row: T) => SortValue;
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
  /** Active sort; when set, rows are sorted by the matching column's sortValue. */
  sort?: SortState | null;
  /** Called with a column key when its sortable header is clicked. */
  onSortChange?: (key: string) => void;
}

function compareSortValues(a: SortValue, b: SortValue): number {
  // Nullish values sort to the end regardless of direction.
  if (a == null && b == null) return 0;
  if (a == null) return 1;
  if (b == null) return -1;
  if (a instanceof Date && b instanceof Date) return a.getTime() - b.getTime();
  if (typeof a === 'number' && typeof b === 'number') return a - b;
  return String(a).localeCompare(String(b));
}

// ---------------------------------------------------------------------------
// AlertCell — use inside a column's render() for the alert column pattern
// ---------------------------------------------------------------------------

interface AlertCellProps {
  type: 'error' | 'warning';
  label: string | readonly string[];
}

function AlertCell({ type, label }: AlertCellProps) {
  const isError = type === 'error';
  const labels = typeof label === 'string' ? [label] : [...label];
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
      <span className="text-p2 flex flex-col font-medium">
        {labels.map((text, index) => (
          <span key={`${text}-${index}`}>
            {text}
            {index < labels.length - 1 ? ',' : ''}
          </span>
        ))}
      </span>
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
  sort,
  onSortChange,
}: DataTableProps<T>) {
  const sortedRows = useMemo(() => {
    if (!sort) return rows;
    const col = columns.find((c) => c.key === sort.key);
    if (!col?.sortValue) return rows;
    const sortValue = col.sortValue;
    const factor = sort.dir === 'asc' ? 1 : -1;
    // Copy so we never mutate the caller's array; stable enough for display.
    return [...rows].sort(
      (a, b) => factor * compareSortValues(sortValue(a), sortValue(b))
    );
  }, [rows, sort, columns]);

  return (
    <div
      className={cn(
        'border-grey-300 overflow-hidden rounded-2xl border bg-white px-6 py-3',
        className
      )}
    >
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-grey-300 border-b">
              {columns.map((col) => {
                const isSorted = sort?.key === col.key;
                return (
                  <th
                    key={col.key}
                    aria-sort={
                      isSorted
                        ? sort?.dir === 'asc'
                          ? 'ascending'
                          : 'descending'
                        : undefined
                    }
                    className={cn(
                      'text-p1 px-4 py-2.5 text-left font-semibold whitespace-nowrap',
                      col.headerClassName
                    )}
                  >
                    {col.sortable ? (
                      <button
                        type="button"
                        onClick={() => onSortChange?.(col.key)}
                        className="hover:text-grey-500 flex cursor-pointer items-center gap-1.5"
                      >
                        {col.header}
                        {isSorted &&
                          (sort?.dir === 'asc' ? (
                            <ChevronUp className="size-4" />
                          ) : (
                            <ChevronDown className="size-4" />
                          ))}
                      </button>
                    ) : (
                      col.header
                    )}
                  </th>
                );
              })}
            </tr>
          </thead>

          <tbody className="divide-grey-300 divide-y">
            {sortedRows.length === 0 ? (
              <tr>
                <td colSpan={columns.length}>{emptyState}</td>
              </tr>
            ) : (
              sortedRows.map((row) => (
                <tr
                  key={getRowKey(row)}
                  data-row-key={getRowKey(row)}
                  className={getRowClassName?.(row)}
                >
                  {columns.map((col) => (
                    <td
                      key={col.key}
                      className={cn(
                        'text-p2 text-grey-500 px-4 py-2.5 whitespace-nowrap',
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
