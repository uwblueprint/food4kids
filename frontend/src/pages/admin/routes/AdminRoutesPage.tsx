import MegaphoneIcon from '@/assets/icons/megaphone.svg?react';
import {
  Button,
  PageHeader,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/common/components';

import { RouteAddressesTab, RouteGroupsTab } from './components';
import { useAddressesTabState, useGroupsTabState } from './hooks';

export const AdminRoutesPage = () => {
  const groupsState = useGroupsTabState();
  const addressesState = useAddressesTabState();

  return (
    <Tabs defaultValue="groups" className="flex flex-col gap-8">
      <PageHeader
        title="Routes"
        actions={
          <Button variant="tertiary" shape="circular">
            <MegaphoneIcon className="size-5 text-blue-300" />
          </Button>
        }
      />

      <TabsList>
        <TabsTrigger value="groups">Groups</TabsTrigger>
        <TabsTrigger value="addresses">Addresses</TabsTrigger>
      </TabsList>

      <TabsContent value="groups">
        <RouteGroupsTab {...groupsState} />
      </TabsContent>
      <TabsContent value="addresses">
        <RouteAddressesTab {...addressesState} />
      </TabsContent>
    </Tabs>
  );
};
