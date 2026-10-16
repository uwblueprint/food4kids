import type { ImportField } from '@/api/generated/types.gen';
import InfoIcon from '@/assets/icons/info-circle.svg?react';
import TrashIcon from '@/assets/icons/trash.svg?react';
import {
  Button,
  Dropdown,
  DropdownContent,
  DropdownItem,
  DropdownTrigger,
  DropdownValue,
  Input,
  MultiSelect,
  Toggle,
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/common/components';
import { cn } from '@/lib/utils';

import {
  COLUMN_LOCKED_MESSAGE,
  createCustomField,
  DATA_TYPE_HELP,
  DATA_TYPES,
  isDeletable,
  isLockedField,
  slugify,
} from '../importFieldOptions';
import { useSettingsForm } from '../useSettingsForm';

const HEADERS = [
  'Column Name',
  'Data Type & Validation',
  'Column Required',
  'Delivery Type',
  'Action',
];

const DataTypeTooltip = () => (
  <Tooltip>
    <TooltipTrigger asChild>
      <button type="button" aria-label="What each data type accepts">
        <InfoIcon className="text-grey-400 size-4" />
      </button>
    </TooltipTrigger>
    <TooltipContent className="bg-grey-500 text-grey-100 max-w-[420px]">
      <ul className="flex flex-col gap-1">
        {DATA_TYPES.map((type) => (
          <li key={type}>
            <span className="font-bold">{type}:</span> {DATA_TYPE_HELP[type]}
          </li>
        ))}
      </ul>
    </TooltipContent>
  </Tooltip>
);

interface RowProps {
  field: ImportField;
  index: number;
  isEditing: boolean;
  deliveryTypes: string[];
  onChange: (index: number, next: ImportField) => void;
  onRemove: (index: number) => void;
}

const ImportFieldRow = ({
  field,
  index,
  isEditing,
  deliveryTypes,
  onChange,
  onRemove,
}: RowProps) => {
  const locked = isLockedField(field);
  const deletable = isDeletable(field);
  const readOnly = !isEditing;
  const cellDisabled = cn(readOnly && 'bg-grey-150 text-grey-400');

  return (
    <div className="grid grid-cols-[2fr_1.5fr_1fr_1.5fr_auto] items-center gap-4">
      <Input
        aria-label={`Column name for ${field.label || 'new column'}`}
        value={field.label ?? ''}
        placeholder="Enter a field name"
        readOnly={readOnly || Boolean(field.builtin)}
        className={cn(cellDisabled, field.builtin && 'bg-grey-150')}
        onChange={(event) =>
          onChange(index, {
            ...field,
            label: event.target.value,
            key: slugify(event.target.value),
          })
        }
      />

      <Dropdown
        value={field.data_type ?? ''}
        onValueChange={(value) =>
          onChange(index, {
            ...field,
            data_type: value as ImportField['data_type'],
          })
        }
        disabled={readOnly || Boolean(field.builtin)}
      >
        <DropdownTrigger
          aria-label={`Data type for ${field.label || 'new column'}`}
          className={cellDisabled}
        >
          <DropdownValue placeholder="Select type" />
        </DropdownTrigger>
        <DropdownContent>
          {DATA_TYPES.map((type) => (
            <DropdownItem key={type} value={type}>
              {type}
            </DropdownItem>
          ))}
        </DropdownContent>
      </Dropdown>

      {/* A locked column is required by the importer itself, so the toggle
       * would not survive a save -- show the state, not a control. */}
      <Toggle
        checked={Boolean(field.required)}
        disabled={readOnly || locked}
        onChange={(checked) => onChange(index, { ...field, required: checked })}
        className={locked ? 'cursor-not-allowed' : undefined}
      />

      <MultiSelect
        aria-label={`Delivery types for ${field.label || 'new column'}`}
        options={deliveryTypes}
        value={field.delivery_types ?? []}
        onChange={(next) => onChange(index, { ...field, delivery_types: next })}
        disabled={readOnly}
        placeholder="Select type"
        className={cellDisabled}
      />

      {isEditing && deletable ? (
        <Button
          variant="destructive"
          shape="circular"
          onClick={() => onRemove(index)}
          aria-label={`Remove ${field.label || 'new column'}`}
        >
          <TrashIcon className="size-5" />
        </Button>
      ) : (
        <span className="size-11" />
      )}
    </div>
  );
};

export const ImportFieldsTable = () => {
  const { isEditing, getField, setField } = useSettingsForm();
  const fields = getField('import_fields') ?? [];
  const deliveryTypes = getField('delivery_types') ?? [];

  const replaceAt = (index: number, next: ImportField) =>
    setField(
      'import_fields',
      fields.map((field, i) => (i === index ? next : field))
    );

  const removeAt = (index: number) =>
    setField(
      'import_fields',
      fields.filter((_, i) => i !== index)
    );

  const addField = () =>
    setField('import_fields', [...fields, createCustomField()]);

  return (
    /* Capped rather than full-bleed: the frames stop the Action column well
     * short of the panel edge, and a table that runs to the edge reads as
     * part of the page chrome. The description wraps earlier still, matching
     * the other sections' 600px measure. */
    <div className="flex max-w-[1040px] flex-col gap-4">
      <div className="flex max-w-[600px] flex-col gap-1">
        <h3 className="text-h3 text-grey-500 font-bold">
          Fields for Spreadsheet Imports
          <span className="text-red ml-1">*</span>
        </h3>
        <p className="text-p2 text-grey-400">
          Choose the fields this system requires when importing spreadsheets
          with addresses. These settings will be applied at your next
          spreadsheet import and will not affect existing addresses.
        </p>
      </div>

      {isEditing && (
        <Button onClick={addField} className="w-fit">
          Add a field
        </Button>
      )}

      <div className="flex flex-col gap-3">
        <div className="grid grid-cols-[2fr_1.5fr_1fr_1.5fr_auto] items-center gap-4">
          {HEADERS.map((header) => (
            <span
              key={header}
              className="text-p3 text-grey-500 flex items-center gap-1 font-bold"
            >
              {header}
              {header === 'Data Type & Validation' && <DataTypeTooltip />}
            </span>
          ))}
        </div>

        {fields.map((field, index) => (
          <Tooltip key={field.key || `new-${index}`}>
            <TooltipTrigger asChild>
              <div>
                <ImportFieldRow
                  field={field}
                  index={index}
                  isEditing={isEditing}
                  deliveryTypes={deliveryTypes}
                  onChange={replaceAt}
                  onRemove={removeAt}
                />
              </div>
            </TooltipTrigger>
            {field.builtin && (
              <TooltipContent className="bg-grey-500 text-grey-100">
                {COLUMN_LOCKED_MESSAGE}
              </TooltipContent>
            )}
          </Tooltip>
        ))}
      </div>
    </div>
  );
};
