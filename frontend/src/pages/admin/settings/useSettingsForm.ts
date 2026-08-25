import { createContext, useContext } from 'react';

import type {
  SystemSettingsRead,
  SystemSettingsUpdate,
} from '@/api/generated/types.gen';

import type { RequiredSettingKey } from './settingsFields';

export interface SettingsFormValue {
  /** The saved row. `undefined` only while the first fetch is in flight. */
  settings: SystemSettingsRead | undefined;
  isLoading: boolean;
  isEditing: boolean;
  isSaving: boolean;
  /** True once any field has been edited away from its saved value. */
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
  /**
   * Required settings that are currently blank. Non-empty means the draft
   * cannot be saved -- the header disables the save button off this, and the
   * panels flag the individual fields.
   */
  missingRequired: RequiredSettingKey[];
  /** Why the last save failed, or null. Cleared when editing is cancelled. */
  saveError: string | null;
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
