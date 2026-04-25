import { useState } from 'react';
import { Link } from 'react-router-dom';

import EditIcon from '@/assets/icons/edit.svg?react';
import { Button, Dropdown } from '@/common/components';
import type { DropdownOption } from '@/common/components/Dropdown';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface RouteConfig {
  delivery_group: string;
  delivery_type: string;
  stops: number;
  route_date: string | null; // ISO date string e.g. "2026-02-16"
  start_time: string | null; // 24h time string e.g. "08:45"
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
  const [configs, setConfigs] = useState<RouteConfig[]>(MOCK_CONFIGS);

  const updateConfig = (index: number, updates: Partial<RouteConfig>) => {
    setConfigs((prev) =>
      prev.map((c, i) => (i === index ? { ...c, ...updates } : c))
    );
  };

  return (
    <>
      {/* Header */}
      <div className="flex flex-col gap-1">
        <h2 className="text-grey-500">Configure Routes</h2>
        <p className="text-p1 text-grey-400">
          Route data has been prefilled based on the imported data. Please
          review the details, make any necessary changes, and select which
          routes to generate.
        </p>
      </div>

      {/* Table */}
      <div className="border-grey-300 overflow-hidden rounded-2xl border bg-white">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-grey-300 border-b">
                {[
                  'Delivery Type',
                  'Delivery Group',
                  'Stops',
                  'Route Date',
                  'Start Time',
                  'Route Count',
                  'End Location',
                ].map((h) => (
                  <th
                    key={h}
                    className="text-p2 px-4 py-3 text-left font-semibold whitespace-nowrap"
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-grey-300 divide-y">
              {configs.map((row, i) => (
                <tr key={row.delivery_group}>
                  {/* Delivery Type */}
                  <td className="text-p2 text-grey-500 px-4 py-3 whitespace-nowrap">
                    {row.delivery_type}
                  </td>

                  {/* Delivery Group */}
                  <td className="text-p2 text-grey-500 px-4 py-3 whitespace-nowrap">
                    {row.delivery_group}
                  </td>

                  {/* Stops */}
                  <td className="text-p2 text-grey-500 px-4 py-3 whitespace-nowrap">
                    {row.stops}
                  </td>

                  {/* Route Date — TODO: add DatePicker component */}
                  <td className="px-4 py-3 whitespace-nowrap" />

                  {/* Start Time — TODO: add TimePicker component */}
                  <td className="px-4 py-3 whitespace-nowrap" />

                  {/* Route Count — inline editable */}
                  <td className="px-4 py-3 whitespace-nowrap">
                    <div className="flex items-center gap-2">
                      <input
                        type="number"
                        min={1}
                        value={row.route_count}
                        onChange={(e) =>
                          updateConfig(i, {
                            route_count: Math.max(1, Number(e.target.value)),
                          })
                        }
                        className="border-grey-300 bg-grey-100 text-p2 text-grey-500 w-14 rounded-lg border px-2 py-1.5 text-center outline-none focus:border-blue-300 focus:ring-1 focus:ring-blue-300"
                      />
                      <EditIcon className="text-grey-400 size-4 shrink-0" />
                    </div>
                  </td>

                  {/* End Location — dropdown */}
                  <td className="px-4 py-3 whitespace-nowrap">
                    <Dropdown
                      options={END_LOCATION_OPTIONS}
                      value={row.end_location}
                      onValueChange={(val) =>
                        updateConfig(i, { end_location: val })
                      }
                      className="w-40"
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between">
        <Button variant="tertiary" asChild>
          <Link to="/admin/routes/generation/review">
            Back to Review Changes
          </Link>
        </Button>
        <Button variant="primary">Continue to Generate Routes</Button>
      </div>
    </>
  );
}
