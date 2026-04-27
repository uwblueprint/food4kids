import { Link } from 'react-router-dom';

import ShareIcon from '@/assets/icons/share.svg?react';
import { Button, Tabs, TabsContent, TabsList, TabsTrigger } from '@/common/components';

import { RouteAddressesTab, RouteGroupsTab } from './components';

const tabActions = (
  <>
    <Button variant="primary" asChild>
      <Link to="/admin/routes/generation">Generate Routes</Link>
    </Button>
    <Button variant="primary" shape="circular">
      <ShareIcon className="size-5" />
    </Button>
  </>
);

export const AdminRoutesPage = () => {
  return (
    <Tabs defaultValue="groups" className="flex flex-col gap-8">
      <h1>Routes</h1>

      <TabsList>
        <TabsTrigger value="groups">Groups</TabsTrigger>
        <TabsTrigger value="addresses">Addresses</TabsTrigger>
      </TabsList>

      <TabsContent value="groups">
        <RouteGroupsTab actions={tabActions} />
      </TabsContent>
      <TabsContent value="addresses">
        <RouteAddressesTab actions={tabActions} />
      </TabsContent>
    </Tabs>
  );
};
