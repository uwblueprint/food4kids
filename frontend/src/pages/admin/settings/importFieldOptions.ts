import type {
  ImportField,
  ImportFieldDataType,
} from '@/api/generated/types.gen';

export const DATA_TYPES: ImportFieldDataType[] = [
  'Text',
  'Address',
  'Number',
  'Phone Number',
  'Email',
  'Yes/No',
];

/** What each data type accepts, shown in the column header's tooltip. */
export const DATA_TYPE_HELP: Record<ImportFieldDataType, string> = {
  Text: 'Accepts any letters, numbers, and words',
  Address: 'Requires a physical address (street, city, area code)',
  Number: 'Only allows whole digits (no letters or symbols)',
  'Phone Number': 'Requires a valid 9-digit number',
  Email: 'Requires a valid email format containing an "@" symbol',
  'Yes/No': 'Accepts yes or no',
};

export const COLUMN_LOCKED_MESSAGE =
  'A column cannot be edited or deleted unless there are no upcoming routes';

export const BUILTIN_COLUMN_MESSAGE =
  "Built-in columns can't be renamed or deleted";

export const REQUIRED_COLUMN_MESSAGE = 'The importer always needs this column';

/**
 * Columns the importer cannot work without, mirroring
 * ``LOCKED_IMPORT_FIELD_KEYS`` on the backend: the API forces these back to
 * required, so the toggle is rendered read-only rather than lying about it.
 */
const LOCKED_KEYS = new Set([
  'contact_name',
  'address',
  'phone_primary',
  'delivery_group',
]);

export const isLockedField = (field: ImportField): boolean =>
  LOCKED_KEYS.has(field.key ?? '');

/** Built-ins back a Location column, so they can be edited but never removed. */
export const isDeletable = (field: ImportField): boolean => !field.builtin;

export function createCustomField(): ImportField {
  return {
    key: '',
    label: '',
    data_type: 'Text',
    required: false,
    delivery_types: [],
    builtin: false,
  };
}

/** A key the backend can address the column by, derived from its label. */
export function slugify(label: string): string {
  return label
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '');
}

/** What is wrong with one column, and which of its controls to outline. */
export interface ImportFieldError {
  message: string;
  label: boolean;
  dataType: boolean;
}

/**
 * Each row's reason the API would reject it, or null for a row that is fine.
 *
 * Caught here rather than on the 422: a nested `loc` like
 * `import_fields.9.key` names no control the page can point at.
 */
export function importFieldErrors(
  fields: ImportField[]
): (ImportFieldError | null)[] {
  const keyCounts = new Map<string, number>();
  for (const field of fields) {
    const key = field.key ?? '';
    if (key) keyCounts.set(key, (keyCounts.get(key) ?? 0) + 1);
  }

  return fields.map((field) => {
    const missingLabel = !field.label?.trim();
    if (missingLabel || !field.data_type) {
      return {
        message: 'Please complete all fields before saving',
        label: missingLabel,
        dataType: !field.data_type,
      };
    }
    // A name of only punctuation slugifies away, leaving no key to address.
    if (!field.key?.trim()) {
      return {
        message: 'Column name needs at least one letter or number',
        label: true,
        dataType: false,
      };
    }
    // Built-ins are read-only, so the clash is flagged on the custom column.
    if (!field.builtin && (keyCounts.get(field.key) ?? 0) > 1) {
      return {
        message: 'Column name must be unique',
        label: true,
        dataType: false,
      };
    }
    return null;
  });
}
