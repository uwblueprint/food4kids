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

/** True once every custom column has a name and a type the API will accept. */
export function isFieldComplete(field: ImportField): boolean {
  return Boolean(field.label?.trim() && field.data_type);
}
