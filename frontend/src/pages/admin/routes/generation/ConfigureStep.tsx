import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import EditIcon from '@/assets/icons/edit.svg?react';
import {
  Button,
  DataTable,
  DatePicker,
  Modal,
  ModalContent,
  ModalDescription,
  ModalFooter,
  ModalHeader,
  ModalTitle,
  Dropdown,
  TextField,
  TimePicker,
} from '@/common/components';
import type { Column, DropdownOption } from '@/common/components';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

// Read-only — comes from the backend (POST /locations/review or similar)
interface RouteGroup {
  delivery_group: string;
  delivery_type: string;
  stops: number;
}

// User-controlled — sent to the generation API
interface RouteFormEntry {
  route_date: Date | undefined;
  start_time: string | undefined;
  route_count: number | undefined;
  end_location: string;
}

type FormState = Record<string, RouteFormEntry>;

// Combined shape for the DataTable row
interface RouteRow extends RouteGroup {
  form: RouteFormEntry;
}

// ---------------------------------------------------------------------------
// Mock API data — replace with real response from backend
// ---------------------------------------------------------------------------

const MOCK_ROUTE_GROUPS: RouteGroup[] = [
  { delivery_group: 'Tuesday A', delivery_type: 'Family', stops: 9 },
  { delivery_group: 'Wednesday B', delivery_type: 'Family', stops: 6 },
  { delivery_group: 'Thursday A', delivery_type: 'Family', stops: 8 },
];

const INITIAL_FORM_STATE: FormState = {
  'Tuesday A': {
    route_date: undefined,
    start_time: undefined,
    route_count: 4,
    end_location: 'Warehouse',
  },
  'Wednesday B': {
    route_date: undefined,
    start_time: undefined,
    route_count: 4,
    end_location: 'Warehouse',
  },
  'Thursday A': {
    route_date: undefined,
    start_time: undefined,
    route_count: 8,
    end_location: 'Warehouse',
  },
};

const END_LOCATION_OPTIONS: DropdownOption[] = [
  { label: 'Warehouse', value: 'Warehouse' },
  { label: 'School', value: 'School' },
];

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function ConfigureStep() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState<FormState>(INITIAL_FORM_STATE);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [leaveOpen, setLeaveOpen] = useState(false);

  const updateEntry = (key: string, updates: Partial<RouteFormEntry>) => {
    setFormData((prev) => ({
      ...prev,
      [key]: { ...prev[key], ...updates },
    }));
  };

  // Merged payload ready to POST to the generation API
  const buildPayload = () =>
    MOCK_ROUTE_GROUPS.map((group) => ({
      ...group,
      ...formData[group.delivery_group],
    }));

  const handleConfirm = () => {
    // TODO: pass buildPayload() to the generation API call
    console.log('Generation payload:', buildPayload());
    setConfirmOpen(false);
    navigate('/admin/routes/generation/generate');
  };

  // Flatten API data + form state into table rows
  const rows: RouteRow[] = MOCK_ROUTE_GROUPS.map((group) => ({
    ...group,
    form: formData[group.delivery_group],
  }));

  const columns: Column<RouteRow>[] = [
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
      render: (row) => (
        <DatePicker
          value={row.form.route_date}
          onChange={(date) =>
            updateEntry(row.delivery_group, { route_date: date })
          }
        />
      ),
    },
    {
      key: 'start_time',
      header: 'Start Time',
      render: (row) => (
        <TimePicker
          value={row.form.start_time}
          onChange={(time) =>
            updateEntry(row.delivery_group, { start_time: time })
          }
        />
      ),
    },
    {
      key: 'route_count',
      header: 'Route Count',
      render: (row) => (
        <TextField
          type="number"
          value={row.form.route_count ?? ''}
          placeholder="0"
          onChange={(e) =>
            updateEntry(row.delivery_group, {
              route_count: e.target.value === '' ? undefined : Number(e.target.value),
            })
          }
          trailingIcon={<EditIcon className="size-4" />}
          className="w-24"
        />
      ),
    },
    {
      key: 'end_location',
      header: 'End Location',
      render: (row) => (
        <Dropdown
          options={END_LOCATION_OPTIONS}
          value={row.form.end_location}
          onValueChange={(val) =>
            updateEntry(row.delivery_group, { end_location: val })
          }
          className="w-40"
        />
      ),
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
          rows={rows}
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
      <Modal open={leaveOpen} onOpenChange={setLeaveOpen}>
        <ModalContent>
          <ModalHeader>
            <ModalTitle>Leave Without Saving</ModalTitle>
            <ModalDescription>
              If you go back now, all the data you entered will be lost. Would
              you still like to go back anyway?
            </ModalDescription>
          </ModalHeader>
          <ModalFooter>
            <Button variant="secondary" onClick={() => setLeaveOpen(false)}>
              Stay on this Page
            </Button>
            <Button
              variant="primary"
              onClick={() => navigate('/admin/routes/generation/review')}
            >
              Leave Anyway
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Generate routes confirmation dialog */}
      <Modal open={confirmOpen} onOpenChange={setConfirmOpen}>
        <ModalContent>
          <ModalHeader>
            <ModalTitle>Continue to Generation</ModalTitle>
            <ModalDescription>
              You're about to generate routes for routes you have selected. This
              action cannot be undone.
            </ModalDescription>
          </ModalHeader>
          <ModalFooter>
            <Button variant="secondary" onClick={() => setConfirmOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleConfirm}>
              Generate Routes
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  );
}
