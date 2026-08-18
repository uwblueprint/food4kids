import { useMemo, useState } from 'react';

import { useDriverList } from '@/api/drivers';
import type { DriverListRead } from '@/api/generated/types.gen';
import PlusIcon from '@/assets/icons/plus.svg?react';
import SearchIcon from '@/assets/icons/search.svg?react';
import {
  Account,
  Button,
  Card,
  CardContent,
  type Column,
  DataTable,
  HighlightText,
  Pagination,
  TableToolbar,
} from '@/common/components';
import {
  clampPage,
  TABLE_PAGE_SIZE,
  useDebouncedValue,
  usePagination,
  useSearch,
  useTableSort,
} from '@/common/hooks';
import { formatPhone, orDash } from '@/common/utils';
import { AnnouncementsBoard } from '@/features/announcements';
import { EmptyState } from '@/pages/admin/routes/components/EmptyState';

import { AddDriverModal, DriverPanel } from './components';

function formatDate(value: string | null | undefined) {
  if (!value) return '—';
  return new Date(`${value}T00:00:00`).toLocaleDateString('en-US', {
    month: '2-digit',
    day: '2-digit',
    year: 'numeric',
  });
}

const SORT_KEYS = {
  name: 'name',
  current_year_km: 'current_year_km',
  last_year_km: 'last_year_km',
  last_delivery: 'last_delivery',
} as const;

export const AdminDriversPage = () => {
  const search = useSearch();
  const searchTerm = useDebouncedValue(search.value).trim();
  const { sort, toggleSort } = useTableSort({ key: 'name', dir: 'asc' });
  const sortBy = SORT_KEYS[sort?.key as keyof typeof SORT_KEYS] ?? 'name';
  const queryKey = JSON.stringify({ searchTerm, sortBy, order: sort?.dir });
  const { page: requestedPage, setPage } = usePagination(queryKey);
  const { data } = useDriverList({
    search: searchTerm || undefined,
    sort_by: sortBy,
    order: sort?.dir ?? 'asc',
    page: requestedPage,
    page_size: TABLE_PAGE_SIZE,
  });
  const rows = useMemo(() => data?.items ?? [], [data]);
  const totalPages = data?.total_pages ?? 0;
  const page = clampPage(requestedPage, totalPages, setPage);
  const [addOpen, setAddOpen] = useState(false);
  const [selected, setSelected] = useState<DriverListRead | null>(null);

  const columns = useMemo<Column<DriverListRead>[]>(
    () => [
      {
        key: 'name',
        header: 'Name',
        sortable: true,
        sortValue: (row) => row.first_name,
        render: (row) => <HighlightText text={row.full_name} query={searchTerm} />,
      },
      { key: 'email', header: 'Email', render: (row) => row.email },
      {
        key: 'phone',
        header: 'Phone number',
        render: (row) => orDash(row.phone && formatPhone(row.phone)),
      },
      {
        key: 'current_year_km',
        header: 'This Year Mileage',
        sortable: true,
        sortValue: (row) => row.current_year_km,
        render: (row) => `${Math.round(row.current_year_km ?? 0)} km`,
      },
      {
        key: 'last_year_km',
        header: 'Last Year Mileage',
        sortable: true,
        sortValue: (row) => row.last_year_km,
        render: (row) => `${Math.round(row.last_year_km ?? 0)} km`,
      },
      {
        key: 'verification',
        header: 'Verification',
        render: (row) => (row.auth_id ? 'Verified' : 'Unverified'),
      },
      {
        key: 'status',
        header: 'Status',
        render: (row) => (row.is_active ? 'Active' : 'Inactive'),
      },
      {
        key: 'last_delivery',
        header: 'Last Delivery',
        sortable: true,
        sortValue: (row) => row.last_delivery,
        render: (row) => formatDate(row.last_delivery),
      },
      {
        key: 'vehicle',
        header: 'Vehicle',
        render: (row) => orDash(row.car_make_model),
      },
    ],
    [searchTerm]
  );

  return (
    <>
      <div className="flex flex-col gap-8">
        <div className="flex items-start justify-between">
          <h1>Driver Management</h1>
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-4">
              <AnnouncementsBoard />
              <Button variant="tertiary" shape="circular">
                <SearchIcon className="size-5 text-blue-300" />
              </Button>
            </div>
            <Account />
          </div>
        </div>

        <Card>
          <CardContent>
            <TableToolbar
              search={search}
              searchPlaceholder="Search for a driver"
              actions={
                <Button
                  variant="primary"
                  shape="circular"
                  aria-label="Add driver"
                  onClick={() => setAddOpen(true)}
                >
                  <PlusIcon className="size-5" />
                </Button>
              }
            />
            <DataTable
              className="rounded-none border-0 px-0"
              columns={columns}
              rows={rows}
              getRowKey={(row) => row.driver_id}
              sort={sort}
              onSortChange={toggleSort}
              onRowClick={setSelected}
              getRowClassName={(row) =>
                `cursor-pointer transition-colors hover:bg-blue-50 focus:bg-blue-50 focus:outline-none ${
                  selected?.driver_id === row.driver_id ? 'bg-blue-50' : ''
                }`
              }
              emptyState={
                <EmptyState
                  image={searchTerm ? 'girl-searching' : 'girl-confused'}
                  title={searchTerm ? 'No drivers found' : 'No drivers yet'}
                  description={
                    searchTerm
                      ? 'Try searching for a different name'
                      : 'Add a driver to get started'
                  }
                />
              }
            />
            <Pagination page={page} totalPages={totalPages} onPageChange={setPage} />
          </CardContent>
        </Card>
      </div>

      <AddDriverModal open={addOpen} onOpenChange={setAddOpen} />
      {selected && <DriverPanel selected={selected} onClose={() => setSelected(null)} />}
    </>
  );
};
