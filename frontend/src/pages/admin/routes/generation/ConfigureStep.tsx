import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import EditIcon from '@/assets/icons/edit.svg?react';
import { Button, DataTable, Dropdown, TextField } from '@/common/components';
import type { Column, DropdownOption } from '@/common/components';

// ---------------------------------------------------------------------------
// TODO: Types
// ---------------------------------------------------------------------------

interface RouteConfig {
  delivery_group: string;
  delivery_type: string;
  stops: number;
  route_date: string | null;
  start_time: string | null;
  route_count: number;
  end_location: string;
}

// ---------------------------------------------------------------------------
// Mock data — replace with real data from POST /locations/review
// ---------------------------------------------------------------------------

const MOCK_CONFIGS: RouteConfig[] = [
  {
    delivery_group: 'Tuesday A',
    delivery_type: 'Family',
    stops: 9,
    route_date: null,
    start_time: null,
    route_count: 4,
    end_location: 'Warehouse',
  },
  {
    delivery_group: 'Wednesday B',
    delivery_type: 'Family',
    stops: 6,
    route_date: null,
    start_time: null,
    route_count: 4,
    end_location: 'Warehouse',
  },
  {
    delivery_group: 'Thursday A',
    delivery_type: 'Family',
    stops: 8,
    route_date: null,
    start_time: null,
    route_count: 8,
    end_location: 'Warehouse',
  },
];

const END_LOCATION_OPTIONS: DropdownOption[] = [
  { label: 'Warehouse', value: 'Warehouse' },
  { label: 'Community Centre', value: 'Community Centre' },
  { label: 'Church', value: 'Church' },
];

// ---------------------------------------------------------------------------
// ConfigureStep
// ---------------------------------------------------------------------------

export function ConfigureStep() {
  const navigate = useNavigate();
  const [configs, setConfigs] = useState<RouteConfig[]>(MOCK_CONFIGS);

  const updateConfig = (index: number, updates: Partial<RouteConfig>) => {
    setConfigs((prev) =>
      prev.map((c, i) => (i === index ? { ...c, ...updates } : c))
    );
  };

  const handleContinue = () => {
    navigate('/admin/routes/generation/generate');
  };

  const columns: Column<RouteConfig>[] = [
    {
      key: 'delivery_type',
      header: 'Delivery Type',
      render: (row) => row.delivery_type,
    },
    {
      key: 'delivery_group',
      header: 'Delivery Group',
      render: (row) => row.delivery_group,
    },
    {
      key: 'stops',
      header: 'Stops',
      render: (row) => String(row.stops),
    },
    {
      key: 'route_date',
      header: 'Route Date',
      render: () => null, // TODO: DatePicker
    },
    {
      key: 'start_time',
      header: 'Start Time',
      render: () => null, // TODO: TimePicker
    },
    {
      key: 'route_count',
      header: 'Route Count',
      render: (row) => {
        const index = configs.indexOf(row);
        return (
          <TextField
            type="number"
            min={1}
            value={row.route_count}
            onChange={(e) =>
              updateConfig(index, {
                route_count: Math.max(1, Number(e.target.value)),
              })
            }
            trailingIcon={<EditIcon className="size-4" />}
            className="w-24"
          />
        );
      },
    },
    {
      key: 'end_location',
      header: 'End Location',
      render: (row) => {
        const index = configs.indexOf(row);
        return (
          <Dropdown
            options={END_LOCATION_OPTIONS}
            value={row.end_location}
            onValueChange={(val) => updateConfig(index, { end_location: val })}
            className="w-40"
          />
        );
      },
    },
  ];

  return (
    <>
      {/* Header */}
      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-1">
          <h2 className="text-grey-500">Configure Routes</h2>
          <p className="text-p1 text-grey-400">
            Route data has been prefilled based on the imported data. Please
            review the details, make any necessary changes, and select which
            routes to generate.
          </p>
        </div>

        <DataTable
          columns={columns}
          rows={configs}
          getRowKey={(row) => row.delivery_group}
        />
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between">
        <Button variant="tertiary" asChild>
          <Link to="/admin/routes/generation/review">
            Back to Review Changes
          </Link>
        </Button>
        <Button variant="primary" onClick={handleContinue}>
          Continue to Generate Routes
        </Button>
      </div>
    </>
  );
}
