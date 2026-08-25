import SearchIcon from '@/assets/icons/search.svg?react';
import {
  Account,
  Banner,
  Button,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/common/components';
import { AnnouncementsBoard } from '@/features/announcements';

import {
  ContactInformationPanel,
  EditingBanner,
  RouteRemindersPanel,
} from './components';
import { SettingsFormProvider } from './SettingsFormProvider';
import { useSettingsForm } from './useSettingsForm';

/**
 * Save, with a tooltip that survives being disabled.
 *
 * A disabled button swallows pointer events, so `title` never fires on it --
 * the trigger has to be a wrapper element. Same pattern as the reminders
 * panel's "Add notification" at its limit.
 */
const SaveButton = ({
  onSave,
  isSaving,
  blockedByRequired,
}: {
  onSave: () => void;
  isSaving: boolean;
  blockedByRequired: boolean;
}) => {
  const button = (
    <Button onClick={onSave} disabled={isSaving || blockedByRequired}>
      {isSaving ? 'Saving…' : 'Save changes'}
    </Button>
  );

  if (!blockedByRequired) return button;

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span>{button}</span>
      </TooltipTrigger>
      <TooltipContent className="bg-grey-500 text-grey-100">
        Fill in every required field before saving.
      </TooltipContent>
    </Tooltip>
  );
};

const SettingsPageHeader = () => {
  const {
    isEditing,
    isLoading,
    isSaving,
    missingRequired,
    startEditing,
    cancelEditing,
    save,
  } = useSettingsForm();

  const blockedByRequired = missingRequired.length > 0;

  return (
    <div className="flex items-start justify-between gap-6">
      <div className="flex items-center gap-8">
        <h1>Settings</h1>
        {isEditing && <EditingBanner onDismiss={cancelEditing} />}
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
          <SaveButton
            onSave={save}
            isSaving={isSaving}
            blockedByRequired={blockedByRequired}
          />
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
          {/* Filled in by the Delivery Defaults PR. */}
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
