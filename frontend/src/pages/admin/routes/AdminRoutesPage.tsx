import { useState } from 'react';
import { Link } from 'react-router-dom';

import FilterLinesIcon from '@/assets/icons/filter-lines.svg?react';
import ShareIcon from '@/assets/icons/share.svg?react';
import {
  Button,
  SearchBar,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/common/components';

import { RouteAddressesTab, RouteGroupsTab } from './components';

export const AdminRoutesPage = () => {
  // TODO: Add search and filter logic
  const [search, setSearch] = useState('');

  return (
    <Tabs defaultValue="groups" className="flex flex-col gap-8">
      {/* Header */}
      <h1 className="text-grey-500">Routes</h1>

      {/* Tabs */}
      <TabsList>
        <TabsTrigger value="groups">Groups</TabsTrigger>
        <TabsTrigger value="addresses">Addresses</TabsTrigger>
      </TabsList>

      {/* Toolbar */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-5">
          <SearchBar
            placeholder="Search anything"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            wrapperClassName="w-64"
          />
          <Button variant="tertiary" shape="circular" className="bg-white">
            <FilterLinesIcon className="size-4" />
          </Button>
        </div>
        <div className="flex items-center gap-4">
          <Button variant="primary" asChild>
            <Link to="/admin/routes/generation">Generate Routes</Link>
          </Button>
          <Button variant="primary" shape="circular">
            <ShareIcon className="size-5" />
          </Button>
        </div>
      </div>

      <TabsContent value="groups">
        <RouteGroupsTab />
      </TabsContent>
      <TabsContent value="addresses">
        <RouteAddressesTab />
      </TabsContent>
    </Tabs>
  );
};
