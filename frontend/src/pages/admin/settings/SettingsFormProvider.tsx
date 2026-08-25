import { type ReactNode, useCallback, useMemo, useState } from 'react';

import type {
  SystemSettingsRead,
  SystemSettingsUpdate,
} from '@/api/generated/types.gen';
import {
  useSystemSettings,
  useUpdateSystemSettings,
} from '@/api/system-settings';

import {
  describeSaveFailure,
  isBlank,
  REQUIRED_SETTING_KEYS,
} from './settingsFields';
import { SettingsFormContext } from './useSettingsForm';

export function SettingsFormProvider({ children }: { children: ReactNode }) {
  const { data: settings, isLoading } = useSystemSettings();
  const updateSettings = useUpdateSystemSettings();

  const [isEditing, setIsEditing] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  // Only edited fields land here, which is exactly the PATCH body: an
  // untouched field is absent rather than sent back at its current value.
  const [draft, setDraft] = useState<SystemSettingsUpdate>({});

  const getField = useCallback(
    <K extends keyof SystemSettingsUpdate>(key: K) => {
      if (key in draft) return draft[key];
      return settings?.[
        key as keyof SystemSettingsRead
      ] as SystemSettingsUpdate[K];
    },
    [draft, settings]
  );

  const setField = useCallback(
    <K extends keyof SystemSettingsUpdate>(
      key: K,
      value: SystemSettingsUpdate[K]
    ) => {
      setDraft((current) => ({ ...current, [key]: value }));
    },
    []
  );

  /* Refuse to open the form until the saved row is in hand. getField prefers
   * the draft, so an edit made during the initial fetch would win over the
   * server's value when it lands -- e.g. adding a reminder to a still-empty
   * list would PATCH a one-item array over the org's real reminders. */
  const startEditing = useCallback(() => {
    if (isLoading) return;
    setIsEditing(true);
  }, [isLoading]);

  const cancelEditing = useCallback(() => {
    setIsEditing(false);
    setDraft({});
    setSaveError(null);
  }, []);

  /* Only fields the admin emptied *in this session* block the save. A field
   * that was already blank when the page loaded must not: a freshly
   * provisioned row has every contact column null (ensure_settings() builds it
   * from model defaults), and blocking on those would leave Save permanently
   * disabled for someone who only came to flip a toggle on another tab. */
  const missingRequired = useMemo(
    () =>
      REQUIRED_SETTING_KEYS.filter(
        (key) => key in draft && isBlank(draft[key])
      ),
    [draft]
  );

  const save = useCallback(() => {
    // The header disables the button, but guard here too so the rule holds for
    // any other caller rather than relying on the UI to enforce it.
    if (missingRequired.length > 0) return;
    setSaveError(null);
    updateSettings.mutate(
      { body: draft },
      {
        onSuccess: () => {
          setIsEditing(false);
          setDraft({});
        },
        onError: (error) => {
          /* Stay in edit mode with the draft intact so the admin can correct
           * the value. Without this the mutation just settles and the page
           * looks unchanged -- indistinguishable from a save that worked. */
          setSaveError(describeSaveFailure(error));
        },
      }
    );
  }, [draft, missingRequired, updateSettings]);

  const value = useMemo(
    () => ({
      settings,
      isLoading,
      isEditing,
      isSaving: updateSettings.isPending,
      isDirty: Object.keys(draft).length > 0,
      missingRequired,
      saveError,
      getField,
      setField,
      startEditing,
      cancelEditing,
      save,
    }),
    [
      settings,
      isLoading,
      isEditing,
      updateSettings.isPending,
      draft,
      missingRequired,
      saveError,
      getField,
      setField,
      startEditing,
      cancelEditing,
      save,
    ]
  );

  return (
    <SettingsFormContext.Provider value={value}>
      {children}
    </SettingsFormContext.Provider>
  );
}
