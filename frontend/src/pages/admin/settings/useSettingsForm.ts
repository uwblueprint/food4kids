import { createContext, useContext } from 'react';

import type { SystemSettingsUpdate } from '@/api/generated/types.gen';

export interface SettingsFormValue {
  isLoading: boolean;
  isEditing: boolean;
  isSaving: boolean;
  /** True once any field holds a value different from what is saved. */
  isDirty: boolean;
  /**
   * The edited value for a field, falling back to what is saved. Every panel
   * reads through this so read mode and edit mode render from one source.
   */
  getField: <K extends keyof SystemSettingsUpdate>(
    key: K
  ) => SystemSettingsUpdate[K];
  setField: <K extends keyof SystemSettingsUpdate>(
    key: K,
    value: SystemSettingsUpdate[K]
  ) => void;
  /** Whether this field has been touched in the current edit session. */
  isEdited: (key: keyof SystemSettingsUpdate) => boolean;
  /** True while a required setting has been emptied, which blocks the save. */
  hasMissingRequired: boolean;
  /** Why the last save failed, or null. Cleared when editing is cancelled. */
  saveError: string | null;
  /**
   * True while a reminder has been added but not given a lead time. Blocks the
   * save until the admin picks one -- or removes the row.
   */
  hasIncompleteReminder: boolean;
  /** True while an added import column has no name yet. */
  hasIncompleteImportField: boolean;
  /** True from a successful save until the next edit, for the saved banner. */
  justSaved: boolean;
  dismissSaved: () => void;
  startEditing: () => void;
  /** Leaves edit mode and throws the draft away. */
  cancelEditing: () => void;
  save: () => void;
}

export const SettingsFormContext = createContext<SettingsFormValue | null>(
  null
);

export function useSettingsForm() {
  const context = useContext(SettingsFormContext);
  if (!context) {
    throw new Error(
      'useSettingsForm must be used within a SettingsFormProvider'
    );
  }
  return context;
}
