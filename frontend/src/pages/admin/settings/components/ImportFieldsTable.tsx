import { type ReactNode, useId } from 'react';

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
  FieldDescription,
  Input,
  MultiSelect,
  Toggle,
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/common/components';
import { cn } from '@/lib/utils';

import {
  BUILTIN_COLUMN_MESSAGE,
  createCustomField,
  DATA_TYPE_HELP,
  DATA_TYPES,
  type ImportFieldError,
  isDeletable,
  isLockedField,
  REQUIRED_COLUMN_MESSAGE,
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

/* The Action column only exists while editing; read-only rows end at
 * Delivery Type. */
const gridColumns = (isEditing: boolean) =>
  cn(
    'grid items-center gap-4',
    isEditing
      ? 'grid-cols-[2fr_1.5fr_1fr_1.5fr_auto]'
      : 'grid-cols-[2fr_1.5fr_1fr_1.5fr]'
  );

const DataTypeTooltip = () => (
  <Tooltip>
    <TooltipTrigger asChild>
      <button type="button" aria-label="What each data type accepts">
        <InfoIcon className="text-grey-400 size-4" />
      </button>
    </TooltipTrigger>
    <TooltipContent className="text-p2 max-w-[560px] rounded-3xl px-6 py-5">
      <ul className="flex flex-col">
        {DATA_TYPES.map((type) => (
          <li key={type}>
            <span className="font-bold">{type}:</span> {DATA_TYPE_HELP[type]}
          </li>
        ))}
      </ul>
    </TooltipContent>
  </Tooltip>
);

/** Explains on hover why a control is locked; renders it alone otherwise. */
const LockedHint = ({
  reason,
  className,
  children,
}: {
  reason: string | null;
  className?: string;
  children: ReactNode;
}) => {
  if (!reason) return children;
  return (
    <Tooltip>
      {/* A wrapper, not asChild: a disabled control fires no hover events. */}
      <TooltipTrigger asChild>
        <div className={className}>{children}</div>
      </TooltipTrigger>
      <TooltipContent>{reason}</TooltipContent>
    </Tooltip>
  );
};

interface RowProps {
  field: ImportField;
  index: number;
  isEditing: boolean;
  deliveryTypes: string[];
  error?: ImportFieldError | null;
  onChange: (index: number, next: ImportField) => void;
  onRemove: (index: number) => void;
}

const ImportFieldRow = ({
  field,
  index,
  isEditing,
  deliveryTypes,
  error,
  onChange,
  onRemove,
}: RowProps) => {
  const errorId = useId();
  const locked = isLockedField(field);
  const deletable = isDeletable(field);
  const builtin = Boolean(field.builtin);
  const readOnly = !isEditing;
  // Grey, not faded: the disabled Dropdown's opacity-60 would wash it out.
  const greyed = 'bg-grey-150 text-grey-400 disabled:opacity-100';
  const cellDisabled = cn(readOnly && greyed);
  // Hints only while editing: read-only, every control is already locked.
  const builtinHint = isEditing && builtin ? BUILTIN_COLUMN_MESSAGE : null;
  const requiredHint = isEditing && locked ? REQUIRED_COLUMN_MESSAGE : null;
  const invalid = 'outline-red focus:outline-red';

  return (
    <div className="flex flex-col gap-2">
      <div className={gridColumns(isEditing)}>
        <LockedHint reason={builtinHint}>
          <Input
            aria-label={`Column name for ${field.label || 'new column'}`}
            aria-invalid={error?.label || undefined}
            aria-describedby={error ? errorId : undefined}
            value={field.label ?? ''}
            placeholder="Enter a field name"
            readOnly={readOnly || builtin}
            className={cn(
              (readOnly || builtin) && greyed,
              error?.label && invalid
            )}
            onChange={(event) =>
              onChange(index, {
                ...field,
                label: event.target.value,
                key: slugify(event.target.value),
              })
            }
          />
        </LockedHint>

        <LockedHint reason={builtinHint}>
          <Dropdown
            value={field.data_type ?? ''}
            onValueChange={(value) =>
              onChange(index, {
                ...field,
                data_type: value as ImportField['data_type'],
              })
            }
            disabled={readOnly || builtin}
          >
            <DropdownTrigger
              aria-label={`Data type for ${field.label || 'new column'}`}
              aria-invalid={error?.dataType || undefined}
              className={cn(
                (readOnly || builtin) && greyed,
                error?.dataType && `${invalid} data-[placeholder]:text-red`
              )}
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
        </LockedHint>

        {/* A locked column is required by the importer itself, so the toggle
         * would not survive a save -- show the state, not a control. The
         * switch has no cell of its own; this matches the MultiSelect's. */}
        <LockedHint reason={requiredHint}>
          <div
            className={cn(
              'border-grey-300 flex h-11 items-center rounded-[30px] border bg-white px-4',
              (readOnly || locked) && greyed
            )}
          >
            <Toggle
              checked={Boolean(field.required)}
              disabled={readOnly || locked}
              onChange={(checked) =>
                onChange(index, { ...field, required: checked })
              }
              className={locked ? 'cursor-not-allowed' : undefined}
            />
          </div>
        </LockedHint>

        <MultiSelect
          aria-label={`Delivery types for ${field.label || 'new column'}`}
          options={deliveryTypes}
          value={field.delivery_types ?? []}
          onChange={(next) =>
            onChange(index, { ...field, delivery_types: next })
          }
          disabled={readOnly}
          placeholder="Select type"
          className={cellDisabled}
        />

        {isEditing &&
          (deletable ? (
            <Button
              variant="destructive"
              shape="circular"
              onClick={() => onRemove(index)}
              aria-label={`Remove ${field.label || 'new column'}`}
            >
              <TrashIcon className="size-5" />
            </Button>
          ) : (
            <LockedHint reason={builtinHint} className="w-fit">
              <Button
                variant="destructive"
                shape="circular"
                disabled
                aria-label={`${field.label} cannot be removed`}
              >
                <TrashIcon className="size-5" />
              </Button>
            </LockedHint>
          ))}
      </div>
      {error && (
        <FieldDescription id={errorId} error>
          {error.message}
        </FieldDescription>
      )}
    </div>
  );
};

export const ImportFieldsTable = () => {
  const { isEditing, getField, setField, importFieldErrors } =
    useSettingsForm();
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

      {/* self-start: the variant's tablet:w-auto would otherwise stretch the
       * button across this flex column. */}
      {isEditing && (
        <Button onClick={addField} className="w-fit self-start">
          Add a field
        </Button>
      )}

      <div className="flex flex-col gap-3">
        <div className={gridColumns(isEditing)}>
          {HEADERS.filter((header) => isEditing || header !== 'Action').map(
            (header) => (
              <span
                key={header}
                className="text-p3 text-grey-500 flex items-center gap-1 font-bold"
              >
                {header}
                {header === 'Data Type & Validation' && <DataTypeTooltip />}
              </span>
            )
          )}
        </div>

        {fields.map((field, index) => (
          // Not field.key: it is re-slugified on every keystroke, and a
          // changing key remounts the row and drops focus.
          <ImportFieldRow
            key={index}
            field={field}
            index={index}
            isEditing={isEditing}
            deliveryTypes={deliveryTypes}
            error={importFieldErrors[index]}
            onChange={replaceAt}
            onRemove={removeAt}
          />
        ))}
      </div>
    </div>
  );
};
