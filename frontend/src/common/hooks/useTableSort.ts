import { useState } from 'react';

import type { SortState } from '@/common/components';

export interface UseTableSortReturn {
  sort: SortState | null;
  /** Toggle sorting for a column: new column → asc, same column → flip dir. */
  toggleSort: (key: string) => void;
}

/**
 * Column-sort state for a DataTable. Clicking a new column sorts it ascending;
 * clicking the active column flips between ascending and descending.
 */
export function useTableSort(
  initial: SortState | null = null
): UseTableSortReturn {
  const [sort, setSort] = useState<SortState | null>(initial);

  const toggleSort = (key: string) =>
    setSort((prev) =>
      prev?.key === key
        ? { key, dir: prev.dir === 'asc' ? 'desc' : 'asc' }
        : { key, dir: 'asc' }
    );

  return { sort, toggleSort };
}
