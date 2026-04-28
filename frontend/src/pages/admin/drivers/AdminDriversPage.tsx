import { useState } from 'react';

import DownloadIcon from '@/assets/icons/download.svg?react';
import MegaphoneIcon from '@/assets/icons/megaphone.svg?react';
import PlusIcon from '@/assets/icons/plus.svg?react';
import { Button, Card, PageHeader, SearchBar } from '@/common/components';

import { AssignRouteDialog } from './components';

export const AdminDriversPage = () => {
  const [search, setSearch] = useState('');
  const [assignDialogOpen, setAssignDialogOpen] = useState(false);

  return (
    <div className="flex flex-col gap-8">
      <PageHeader
        title="Driver Management"
        actions={
          <Button variant="tertiary" shape="circular">
            <MegaphoneIcon className="size-5" />
          </Button>
        }
      />

      <Card>
        <div className="mb-5 flex items-center justify-between">
          <SearchBar
            placeholder="Search for a driver"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            wrapperClassName="w-64"
          />
          <div className="flex items-center gap-4">
            <Button variant="primary" shape="circular" onClick={() => setAssignDialogOpen(true)}>
              <PlusIcon className="size-5" />
            </Button>
            <Button variant="primary" shape="circular">
              <DownloadIcon className="size-5" />
            </Button>
          </div>
        </div>
        <div>TODO</div>
      </Card>

      <AssignRouteDialog
        open={assignDialogOpen}
        onOpenChange={setAssignDialogOpen}
      />
    </div>
  );
};
