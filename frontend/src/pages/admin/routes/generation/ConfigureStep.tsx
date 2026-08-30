import { useMemo, useState } from 'react';
import { Navigate, useNavigate, useOutletContext } from 'react-router-dom';

import { useLocationGroups, useSystemSettings } from '@/api';
import EditIcon from '@/assets/icons/edit.svg?react';
import type { Column } from '@/common/components';
import {
  Banner,
  Button,
  ConfirmModal,
  DataTable,
  DatePicker,
  Input,
  Spinner,
  TimePicker,
} from '@/common/components';
import { cn } from '@/lib/utils';

import type { GenerationOutletContext } from './AdminRoutesGenerationLayout';
import { GenerationFooter } from './GenerationFooter';

interface RouteFormEntry {
  name: string;
  routeDate: Date | undefined;
  startTime: string;
  routeCount: number | undefined;
  returnToWarehouse: boolean;
}

type FormState = Record<string, RouteFormEntry>;

interface RouteRow {
  name: string;
  deliveryGroup: string;
  deliveryType: string;
  stops: number;
  form: RouteFormEntry;
}

const WEEKDAYS: Record<string, number> = {
  sunday: 0,
  monday: 1,
  tuesday: 2,
  wednesday: 3,
  thursday: 4,
  friday: 5,
  saturday: 6,
};

function nextRouteDate(groupName: string, today = new Date()): Date {
  const weekdayName = groupName
    .toLowerCase()
    .match(
      /\b(sunday|monday|tuesday|wednesday|thursday|friday|saturday)\b/
    )?.[1];
  const targetDay = weekdayName ? WEEKDAYS[weekdayName] : undefined;
  const result = new Date(today);
  result.setHours(0, 0, 0, 0);

  if (targetDay === undefined) {
    result.setDate(result.getDate() + 1);
    return result;
  }

  let daysUntil = (targetDay - result.getDay() + 7) % 7;
  if (daysUntil === 0) daysUntil = 7;
  result.setDate(result.getDate() + daysUntil);
  return result;
}

function normalizeTime(value: string | null | undefined): string {
  return value?.slice(0, 5) || '09:00';
}

function routeStartDateTime(date: Date, time: string): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}T${time}:00`;
}

function defaultRouteName(groupName: string, routeDate: Date): string {
  const date = routeDate.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  });
  return `${date} - ${groupName}`;
}

function ReturnToggle({
  checked,
  disabled = false,
  onChange,
}: {
  checked: boolean;
  disabled?: boolean;
  onChange: (checked: boolean) => void;
}) {
  return (
    <div
      className={cn(
        'flex items-center gap-2',
        disabled ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'
      )}
    >
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        onClick={() => onChange(!checked)}
        className={cn(
          'relative h-5 w-9 rounded-full transition-colors',
          checked ? 'bg-blue-300' : 'bg-grey-300'
        )}
      >
        <span
          className={cn(
            'absolute top-0.5 left-0 size-4 rounded-full bg-white transition-transform',
            checked ? 'translate-x-[18px]' : 'translate-x-0.5'
          )}
        />
      </button>
      <span className="text-p2">{checked ? 'Yes' : 'No'}</span>
    </div>
  );
}

export function ConfigureStep() {
  const navigate = useNavigate();
  const { file, reviewResult, selectedDeliveryType, setRouteGenerationInputs } =
    useOutletContext<GenerationOutletContext>();
  const { data: systemSettings } = useSystemSettings();
  const {
    data: locationGroups,
    isPending: groupsPending,
    isError: groupsError,
  } = useLocationGroups();

  const [formData, setFormData] = useState<FormState>({});
  const [deselectedGroups, setDeselectedGroups] = useState<Set<string>>(
    new Set()
  );
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [leaveOpen, setLeaveOpen] = useState(false);

  const importedGroupCounts = useMemo(() => {
    const counts = new Map<string, number>();
    for (const row of reviewResult?.rows ?? []) {
      const groupName = row.location.delivery_group?.trim();
      if (!groupName || row.alerts.length > 0) continue;
      counts.set(groupName, (counts.get(groupName) ?? 0) + 1);
    }
    return counts;
  }, [reviewResult]);

  const importedGroups = useMemo(
    () =>
      (locationGroups ?? []).filter((group) =>
        importedGroupCounts.has(group.name)
      ),
    [importedGroupCounts, locationGroups]
  );

  if (!file || !reviewResult || !selectedDeliveryType) {
    return <Navigate to="/admin/routes/generation/import" replace />;
  }

  const defaultEntry = (groupName: string): RouteFormEntry => {
    const stops = importedGroupCounts.get(groupName) ?? 0;
    const boxesPerCar = systemSettings?.boxes_per_car;
    const routeDate = nextRouteDate(groupName);
    return {
      name: defaultRouteName(groupName, routeDate),
      routeDate,
      startTime: normalizeTime(systemSettings?.route_start_time),
      routeCount:
        boxesPerCar && boxesPerCar > 0
          ? Math.max(1, Math.ceil(stops / boxesPerCar))
          : 1,
      returnToWarehouse: false,
    };
  };

  const getEntry = (groupName: string) =>
    formData[groupName] ?? defaultEntry(groupName);

  const updateEntry = (groupName: string, updates: Partial<RouteFormEntry>) => {
    setFormData((previous) => ({
      ...previous,
      [groupName]: {
        ...(previous[groupName] ?? defaultEntry(groupName)),
        ...updates,
      },
    }));
  };

  const toggleGroup = (groupName: string) => {
    setDeselectedGroups((previous) => {
      const next = new Set(previous);
      if (next.has(groupName)) next.delete(groupName);
      else next.add(groupName);
      return next;
    });
  };

  const rows: RouteRow[] = importedGroups.map((group) => ({
    name: getEntry(group.name).name,
    deliveryGroup: group.name,
    deliveryType: selectedDeliveryType,
    stops: importedGroupCounts.get(group.name) ?? group.num_locations,
    form: getEntry(group.name),
  }));

  const selectedRows = rows.filter(
    (row) => !deselectedGroups.has(row.deliveryGroup)
  );
  const allSelected = rows.length > 0 && selectedRows.length === rows.length;

  const toggleAllGroups = () => {
    setDeselectedGroups(
      allSelected ? new Set(rows.map((row) => row.deliveryGroup)) : new Set()
    );
  };
  const missingGroups = [...importedGroupCounts.keys()].filter(
    (name) => !importedGroups.some((group) => group.name === name)
  );
  const canContinue =
    selectedRows.length > 0 &&
    missingGroups.length === 0 &&
    selectedRows.every(
      (row) =>
        row.form.name.trim().length > 0 &&
        row.form.routeDate &&
        row.form.startTime &&
        row.form.routeCount !== undefined &&
        row.form.routeCount > 0 &&
        row.form.routeCount <= row.stops
    );

  const handleConfirm = () => {
    if (!canContinue) return;

    setRouteGenerationInputs(
      selectedRows.map((row) => {
        const group = importedGroups.find(
          (candidate) => candidate.name === row.deliveryGroup
        );
        if (!group || !row.form.routeDate || !row.form.routeCount) {
          throw new Error('Selected route group is missing required settings');
        }

        return {
          location_group: {
            location_group_id: group.location_group_id,
            name: row.form.name,
            color: group.color,
            notes: group.notes,
          },
          settings: {
            route_start_time: routeStartDateTime(
              row.form.routeDate,
              row.form.startTime
            ),
            num_routes: row.form.routeCount,
            return_to_warehouse: row.form.returnToWarehouse,
            max_boxes_per_driver: systemSettings?.boxes_per_car,
            children_per_box: systemSettings?.children_per_box,
            service_time_minutes: systemSettings?.dropoff_minutes,
          },
        };
      })
    );
    setConfirmOpen(false);
    navigate('/admin/routes/generation/generate');
  };

  const columns: Column<RouteRow>[] = [
    {
      key: 'selected',
      header: (
        <input
          type="checkbox"
          checked={allSelected}
          onChange={toggleAllGroups}
          aria-label={
            allSelected
              ? 'Deselect all route groups'
              : 'Select all route groups'
          }
          className="size-4 cursor-pointer rounded-[4px] accent-blue-300"
        />
      ),
      headerClassName: 'w-8 px-2',
      cellClassName: 'w-8 px-2',
      render: (row) => (
        <input
          type="checkbox"
          checked={!deselectedGroups.has(row.deliveryGroup)}
          onChange={() => toggleGroup(row.deliveryGroup)}
          aria-label={`Generate routes for ${row.deliveryGroup}`}
          className="size-4 cursor-pointer rounded-[4px] accent-blue-300"
        />
      ),
    },
    {
      key: 'name',
      header: 'Name',
      render: (row) => (
        <div className="relative w-48">
          <Input
            value={row.form.name}
            disabled={deselectedGroups.has(row.deliveryGroup)}
            aria-label={`Name for ${row.deliveryGroup}`}
            onChange={(event) =>
              updateEntry(row.deliveryGroup, { name: event.target.value })
            }
            className="py-2 pr-9"
          />
          <EditIcon className="text-grey-500 pointer-events-none absolute top-1/2 right-3 size-4 -translate-y-1/2" />
        </div>
      ),
    },
    {
      key: 'delivery_type',
      header: 'Delivery Type',
      render: (row) => row.deliveryType,
    },
    {
      key: 'delivery_group',
      header: 'Delivery Group',
      render: (row) => row.deliveryGroup,
    },
    { key: 'stops', header: 'Stops', render: (row) => String(row.stops) },
    {
      key: 'route_date',
      header: 'Date',
      render: (row) => (
        <DatePicker
          value={row.form.routeDate}
          onChange={(routeDate) => {
            const previousDefaultName = row.form.routeDate
              ? defaultRouteName(row.deliveryGroup, row.form.routeDate)
              : undefined;
            updateEntry(row.deliveryGroup, {
              routeDate,
              ...(routeDate && row.form.name === previousDefaultName
                ? { name: defaultRouteName(row.deliveryGroup, routeDate) }
                : {}),
            });
          }}
          disabled={deselectedGroups.has(row.deliveryGroup)}
          className="w-36"
        />
      ),
    },
    {
      key: 'start_time',
      header: 'Start Time',
      render: (row) => (
        <TimePicker
          value={row.form.startTime}
          onChange={(startTime) =>
            updateEntry(row.deliveryGroup, { startTime })
          }
          disabled={deselectedGroups.has(row.deliveryGroup)}
          className="w-32"
        />
      ),
    },
    {
      key: 'route_count',
      header: 'Routes',
      render: (row) => (
        <div className="relative w-20">
          <Input
            type="number"
            min={1}
            max={row.stops}
            value={row.form.routeCount ?? ''}
            disabled={deselectedGroups.has(row.deliveryGroup)}
            aria-label={`Route count for ${row.deliveryGroup}`}
            onChange={(event) =>
              updateEntry(row.deliveryGroup, {
                routeCount:
                  event.target.value === ''
                    ? undefined
                    : Number(event.target.value),
              })
            }
            className="py-2 pr-8"
          />
          <EditIcon className="text-grey-400 pointer-events-none absolute top-1/2 right-3 size-4 -translate-y-1/2" />
        </div>
      ),
    },
    {
      key: 'return_to_warehouse',
      header: 'End at Warehouse',
      render: (row) => (
        <ReturnToggle
          checked={row.form.returnToWarehouse}
          disabled={deselectedGroups.has(row.deliveryGroup)}
          onChange={(returnToWarehouse) =>
            updateEntry(row.deliveryGroup, { returnToWarehouse })
          }
        />
      ),
    },
  ];

  return (
    <>
      <section className="flex flex-col gap-4">
        <div className="flex flex-col gap-1">
          <h2 className="text-grey-500">Edit Route Groups</h2>
          <p className="text-p1 text-grey-500">
            Route groups were created from the imported data. Please review the
            details, make necessary changes, and select which routes to
            generate.
          </p>
        </div>

        {groupsError && (
          <Banner variant="error">
            Could not load the imported route groups. Please try again.
          </Banner>
        )}
        {missingGroups.length > 0 && !groupsPending && (
          <Banner variant="error">
            Some imported route groups could not be loaded. Go back and apply
            the import again.
          </Banner>
        )}
        {groupsPending ? (
          <div className="flex justify-center py-16">
            <Spinner size="lg" />
          </div>
        ) : (
          <DataTable
            columns={columns}
            rows={rows}
            getRowKey={(row) => row.deliveryGroup}
          />
        )}
      </section>

      <GenerationFooter>
        <Button variant="tertiary" onClick={() => setLeaveOpen(true)}>
          Back to review changes
        </Button>
        <Button
          variant="primary"
          disabled={!canContinue}
          onClick={() => setConfirmOpen(true)}
        >
          Continue to generate routes
        </Button>
      </GenerationFooter>

      <ConfirmModal
        open={leaveOpen}
        onOpenChange={setLeaveOpen}
        onConfirm={() => navigate('/admin/routes/generation/review')}
        title="Leave without Saving"
        description="If you go back now, all the data you entered will be lost. Would you still like to go back anyway?"
        cancelLabel="Stay on this page"
        confirmLabel="Leave anyway"
      />

      <ConfirmModal
        open={confirmOpen}
        onOpenChange={setConfirmOpen}
        onConfirm={handleConfirm}
        title="Continue to Generation"
        description="You're about to generate delivery routes for routes you have selected. This action cannot be undone."
        confirmLabel="Generate routes"
      />
    </>
  );
}
