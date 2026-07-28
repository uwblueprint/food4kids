import { useSearchParams } from 'react-router-dom';

import {
  Account,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/common/components';
import { AnnouncementsBoard } from '@/features/announcements';

import {
  RouteAddressesTab,
  RouteGroupsTab,
  RouteRoutesTab,
} from './components';
import { useAddressesTabState, useGroupsTabState } from './hooks';

const TABS = ['groups', 'routes', 'addresses'] as const;
type RoutesTab = (typeof TABS)[number];

const isTab = (value: string | null): value is RoutesTab =>
  TABS.includes(value as RoutesTab);

export const AdminRoutesPage = () => {
  const groupsState = useGroupsTabState();
  const addressesState = useAddressesTabState();

  // The tab lives in the URL so a refresh, a bookmark, or a link keeps the
  // reader where they were. An absent or unrecognised ?tab= falls back to
  // Groups rather than erroring: the query string is reader input, and the
  // page has a sensible default. Replaced rather than pushed — Back should
  // leave the page, not walk back through the tabs you looked at.
  const [searchParams, setSearchParams] = useSearchParams();
  const param = searchParams.get('tab');
  const tab: RoutesTab = isTab(param) ? param : 'groups';

  const handleTabChange = (value: string) => {
    const next = new URLSearchParams(searchParams);
    next.set('tab', value);
    setSearchParams(next, { replace: true });
  };

  return (
    <Tabs
      value={tab}
      onValueChange={handleTabChange}
      className="flex flex-col gap-8"
    >
      <div className="flex items-start justify-between">
        <h1>Routes</h1>
        <div className="flex items-center gap-6">
          <AnnouncementsBoard />
          <Account />
        </div>
      </div>

      <TabsList>
        <TabsTrigger value="groups">Groups</TabsTrigger>
        <TabsTrigger value="routes">Routes</TabsTrigger>
        <TabsTrigger value="addresses">Addresses</TabsTrigger>
      </TabsList>

      <TabsContent value="groups">
        <RouteGroupsTab {...groupsState} />
      </TabsContent>
      <TabsContent value="routes">
        <RouteRoutesTab />
      </TabsContent>
      <TabsContent value="addresses">
        <RouteAddressesTab {...addressesState} />
      </TabsContent>
    </Tabs>
  );
};
