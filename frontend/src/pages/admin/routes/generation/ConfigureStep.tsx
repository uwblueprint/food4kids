import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import EditIcon from '@/assets/icons/edit.svg?react';
import {
  Button,
  DataTable,
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  Dropdown,
  TextField,
  TimePicker,
} from '@/common/components';
import type { Column, DropdownOption } from '@/common/components';
import { DatePicker } from '@/common/components';

// ---------------------------------------------------------------------------
// TODO: Hook up to backend API and define actual types
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

// TODO: hook up form state for dates and times
export function ConfigureStep() {
  const navigate = useNavigate();
  const [configs, setConfigs] = useState<RouteConfig[]>(MOCK_CONFIGS);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [leaveOpen, setLeaveOpen] = useState(false);

  const updateConfig = (index: number, updates: Partial<RouteConfig>) => {
    setConfigs((prev) =>
      prev.map((c, i) => (i === index ? { ...c, ...updates } : c))
    );
  };

  const handleConfirm = () => {
    setConfirmOpen(false);
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
      render: () => <DatePicker />,
    },
    {
      key: 'start_time',
      header: 'Start Time',
      render: () => <TimePicker />,
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
        <Button variant="tertiary" onClick={() => setLeaveOpen(true)}>
          Back to Review Changes
        </Button>
        <Button variant="primary" onClick={() => setConfirmOpen(true)}>
          Continue to Generate Routes
        </Button>
      </div>

      {/* Leave without saving dialog */}
      <Dialog open={leaveOpen} onOpenChange={setLeaveOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Leave Without Saving</DialogTitle>
            <DialogDescription>
              If you go back now, all the data you entered will be lost. Would
              you still like to go back anyway?
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="secondary" onClick={() => setLeaveOpen(false)}>
              Stay on this Page
            </Button>
            <Button
              variant="primary"
              onClick={() => navigate('/admin/routes/generation/review')}
            >
              Leave Anyway
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Generate routes confirmation dialog */}
      <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Continue to Generation</DialogTitle>
            <DialogDescription>
              You're about to generate routes for routes you have selected. This
              action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="secondary" onClick={() => setConfirmOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleConfirm}>
              Generate Routes
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
