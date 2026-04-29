import { useState } from 'react';

import DownloadIcon from '@/assets/icons/download.svg?react';
import MegaphoneIcon from '@/assets/icons/megaphone.svg?react';
import PlusIcon from '@/assets/icons/plus.svg?react';
import SearchIcon from '@/assets/icons/search.svg?react';
import { Account, Button, Card, SearchBar } from '@/common/components';
import { useSearch } from '@/common/hooks';

import { AssignRouteModal } from './components';

export const AdminDriversPage = () => {
  const search = useSearch();
  const [assignDialogOpen, setAssignDialogOpen] = useState(false);

  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-start justify-between">
        <h1>Driver Management</h1>
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

      <Card>
        <div className="mb-5 flex items-center justify-between">
          <SearchBar
            placeholder="Search for a driver"
            {...search}
            wrapperClassName="w-64"
          />
          <div className="flex items-center gap-4">
            <Button
              variant="primary"
              shape="circular"
              onClick={() => setAssignDialogOpen(true)}
            >
              <PlusIcon className="size-5" />
            </Button>
            <Button variant="primary" shape="circular">
              <DownloadIcon className="size-5" />
            </Button>
          </div>
        </div>
        <div>TODO</div>
      </Card>

      <AssignRouteModal
        open={assignDialogOpen}
        onOpenChange={setAssignDialogOpen}
      />
    </div>
  );
};
