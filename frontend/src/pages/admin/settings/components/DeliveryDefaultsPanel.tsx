import { useState } from 'react';

import type { SystemSettingsUpdate } from '@/api/generated/types.gen';
import { Button, Field, FieldLabel, Input, Tag } from '@/common/components';
import { formatPhone } from '@/common/utils';
import { cn } from '@/lib/utils';

import { useSettingsForm } from '../useSettingsForm';
import { ImportFieldsTable } from './ImportFieldsTable';

interface NumericSetting {
  key: 'boxes_per_car' | 'children_per_box' | 'dropoff_minutes';
  label: string;
  hint: string;
  min: number;
}

/* Minimums mirror the model: boxes_per_car and children_per_box are ge=1
 * (a car holding no boxes cannot hold a route; a zero divisor breaks the box
 * count), dropoff_minutes is ge=0. */
const NUMERIC_SETTINGS: NumericSetting[] = [
  {
    key: 'boxes_per_car',
    label: 'Boxes an average car can hold',
    hint: 'Default: 10 boxes',
    min: 1,
  },
  {
    key: 'children_per_box',
    label: 'Number of children one box can feed',
    hint: 'Default: 2 children per box',
    min: 1,
  },
  {
    key: 'dropoff_minutes',
    label: 'Minutes to drop off at each location',
    hint: 'Default: 3 minutes',
    min: 0,
  },
];

const NumericRow = ({ setting }: { setting: NumericSetting }) => {
  const { isEditing, getField, setField } = useSettingsForm();
  const value = getField(setting.key);

  return (
    <div className="flex items-start justify-between gap-8">
      <div className="flex flex-col gap-0.5">
        <span className="text-h3 text-grey-500 font-bold">
          {setting.label}
          {setting.min > 0 && <span className="text-red ml-1">*</span>}
        </span>
        <span className="text-p3 text-grey-400">{setting.hint}</span>
      </div>
      <Input
        type="number"
        min={setting.min}
        aria-label={setting.label}
        readOnly={!isEditing}
        className={cn('w-16 text-center', !isEditing && 'bg-grey-150')}
        value={value ?? ''}
        onChange={(event) => {
          const next = event.target.value;
          setField(setting.key, next === '' ? null : Number(next));
        }}
      />
    </div>
  );
};

const TextRow = ({
  settingKey,
  label,
  hint,
  placeholder,
  required,
  format,
}: {
  settingKey: Extract<
    keyof SystemSettingsUpdate,
    'support_phone' | 'warehouse_location'
  >;
  label: string;
  hint: string;
  placeholder: string;
  required?: boolean;
  format?: (value: string) => string;
}) => {
  const { isEditing, getField, setField } = useSettingsForm();
  const stored = getField(settingKey) ?? '';

  return (
    <Field className="max-w-[600px]">
      <div className="flex flex-col gap-0.5">
        <FieldLabel htmlFor={`settings-${settingKey}`} required={required}>
          {label}
        </FieldLabel>
        <span className="text-p3 text-grey-400">{hint}</span>
      </div>
      <Input
        id={`settings-${settingKey}`}
        readOnly={!isEditing}
        className={cn(!isEditing && 'bg-grey-150 text-grey-400')}
        placeholder={isEditing ? placeholder : undefined}
        value={format ? format(stored) : stored}
        onChange={(event) => setField(settingKey, event.target.value || null)}
      />
    </Field>
  );
};

const DeliveryTypesRow = () => {
  const { isEditing, getField, setField } = useSettingsForm();
  const types = getField('delivery_types') ?? [];
  const [draft, setDraft] = useState('');

  const trimmed = draft.trim();
  const duplicate = types.some(
    (type) => type.toLowerCase() === trimmed.toLowerCase()
  );
  const error =
    trimmed && duplicate ? 'Delivery type already exists' : undefined;

  const add = () => {
    if (!trimmed || duplicate) return;
    setField('delivery_types', [...types, trimmed]);
    setDraft('');
  };

  return (
    <div className="flex max-w-[600px] flex-col gap-2">
      <div className="flex flex-col gap-0.5">
        <span className="text-h3 text-grey-500 font-bold">
          Delivery Types<span className="text-red ml-1">*</span>
        </span>
        <span className="text-p3 text-grey-400">
          Customize which Delivery Type categories are shown on routes.
        </span>
      </div>

      {isEditing && (
        <div className="flex items-start gap-4">
          <Input
            aria-label="Add a new delivery type"
            placeholder="Add a new delivery type here"
            value={draft}
            error={error}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter') {
                event.preventDefault();
                add();
              }
            }}
          />
          <Button onClick={add} disabled={!trimmed || duplicate}>
            Add type
          </Button>
        </div>
      )}

      <div className="flex flex-wrap gap-2">
        {types.map((type) => (
          <Tag
            key={type}
            variant="primary"
            /* Removing the last type would leave the roster with no category
             * to import into, which the API rejects outright. */
            onRemove={
              isEditing && types.length > 1
                ? () =>
                    setField(
                      'delivery_types',
                      types.filter((item) => item !== type)
                    )
                : undefined
            }
          >
            {type}
          </Tag>
        ))}
      </div>
    </div>
  );
};

export const DeliveryDefaultsPanel = () => {
  return (
    <div className="flex flex-col gap-8">
      <div className="flex max-w-[600px] flex-col gap-4">
        {NUMERIC_SETTINGS.map((setting) => (
          <NumericRow key={setting.key} setting={setting} />
        ))}
      </div>

      <TextRow
        settingKey="support_phone"
        label="Support Phone Number"
        hint="This is the default phone number drivers can call for help while delivering."
        placeholder="Enter phone number"
        required
        format={formatPhone}
      />

      <TextRow
        settingKey="warehouse_location"
        label="Warehouse Location"
        hint="If enabled for a route in Route Generation, that route will start and end at this address."
        placeholder="Enter address"
        required
      />

      <DeliveryTypesRow />
      <ImportFieldsTable />
    </div>
  );
};
