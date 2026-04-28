import { Account, Button } from '@/common/components';
import MegaphoneIcon from '@/assets/icons/megaphone.svg?react';
import SearchIcon from '@/assets/icons/search.svg?react';

export const AdminSettingsPage = () => {
  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-start justify-between">
        <h1>Settings</h1>
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-4">
            <Button variant="tertiary" shape="circular">
              <MegaphoneIcon className="size-5 text-blue-300" />
            </Button>
            <Button variant="tertiary" shape="circular">
              <SearchIcon className="size-5 text-blue-300" />
            </Button>
          </div>
          <Account />
        </div>
      </div>
      <div>TODO</div>
    </div>
  );
};
