import { useState } from 'react';

import SearchIcon from '@/assets/icons/search.svg?react';
import {
  Account,
  Banner,
  Button,
  ConfirmModal,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/common/components';
import { AnnouncementsBoard } from '@/features/announcements';

import {
  BlockedButton,
  ContactInformationPanel,
  DeliveryDefaultsPanel,
  RouteRemindersPanel,
  SettingsBanner,
} from './components';
import { SettingsFormProvider } from './SettingsFormProvider';
import { useSettingsForm } from './useSettingsForm';

const SettingsPageHeader = () => {
  const {
    isEditing,
    isLoading,
    isSaving,
    isDirty,
    hasMissingRequired,
    hasIncompleteReminder,
    hasIncompleteImportField,
    justSaved,
    dismissSaved,
    startEditing,
    cancelEditing,
    save,
  } = useSettingsForm();

  const [confirmDiscard, setConfirmDiscard] = useState(false);

  const handleStopEditing = () => {
    if (isDirty) {
      setConfirmDiscard(true);
      return;
    }
    cancelEditing();
  };

  /* Reminders first: an unset notification is the more specific problem, and
   * the fix for it is different -- pick a day, or remove the row. */
  const blockedReason = hasIncompleteReminder
    ? 'Choose how many days before for every notification, or remove it.'
    : hasIncompleteImportField
      ? 'Please complete all fields before saving.'
      : hasMissingRequired
        ? 'Fill in every required field before saving.'
        : null;

  return (
    <div className="flex items-start justify-between gap-6">
      <div className="flex items-center gap-8">
        <h1>Settings</h1>
        {isEditing && (
          <SettingsBanner
            variant="editing"
            onDismiss={handleStopEditing}
            dismissLabel="Stop editing"
          />
        )}
        {!isEditing && justSaved && (
          <SettingsBanner
            variant="saved"
            onDismiss={dismissSaved}
            dismissLabel="Dismiss"
          />
        )}
        {/* Offering "Save changes" while the draft cannot be saved would be a
         * dead button, so a blocked form gets a discard-only prompt. */}
        {blockedReason ? (
          <ConfirmModal
            open={confirmDiscard}
            onOpenChange={setConfirmDiscard}
            title="Unsaved Changes"
            description={`${blockedReason} Leaving now will discard your changes.`}
            confirmLabel="Discard changes"
            confirmVariant="destructive"
            onConfirm={() => {
              setConfirmDiscard(false);
              cancelEditing();
            }}
            onCancel={() => setConfirmDiscard(false)}
          />
        ) : (
          <ConfirmModal
            open={confirmDiscard}
            onOpenChange={setConfirmDiscard}
            title="Unsaved Changes"
            description="You have unsaved changes. Leaving this page will discard them. Do you want to save before exiting?"
            confirmLabel="Save changes"
            cancelLabel="Discard"
            onConfirm={() => {
              setConfirmDiscard(false);
              save();
            }}
            onCancel={() => {
              setConfirmDiscard(false);
              cancelEditing();
            }}
          />
        )}
      </div>
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-4">
          <AnnouncementsBoard />
          <Button variant="tertiary" shape="circular">
            <SearchIcon className="size-5 text-blue-300" />
          </Button>
        </div>
        <Account />
        {isEditing ? (
          <BlockedButton
            onClick={save}
            disabled={isSaving}
            blockedReason={blockedReason}
          >
            {isSaving ? 'Saving…' : 'Save changes'}
          </BlockedButton>
        ) : (
          <Button onClick={startEditing} disabled={isLoading}>
            Edit settings
          </Button>
        )}
      </div>
    </div>
  );
};

const AdminSettingsPageContent = () => {
  const { saveError } = useSettingsForm();

  return (
    <div className="flex flex-col gap-8">
      <SettingsPageHeader />
      {saveError && (
        <Banner variant="error" className="max-w-[600px]">
          {saveError}
        </Banner>
      )}
      <Tabs defaultValue="delivery-defaults">
        <TabsList>
          <TabsTrigger value="delivery-defaults">Delivery Defaults</TabsTrigger>
          <TabsTrigger value="route-reminders">Route Reminders</TabsTrigger>
          <TabsTrigger value="contact-information">
            Contact Information
          </TabsTrigger>
        </TabsList>
        <TabsContent value="delivery-defaults">
          <DeliveryDefaultsPanel />
        </TabsContent>
        <TabsContent value="route-reminders">
          <RouteRemindersPanel />
        </TabsContent>
        <TabsContent value="contact-information">
          <ContactInformationPanel />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export const AdminSettingsPage = () => {
  return (
    <SettingsFormProvider>
      <AdminSettingsPageContent />
    </SettingsFormProvider>
  );
};
