import { useState } from 'react';
import { Link } from 'react-router-dom';

import FilterLinesIcon from '@/assets/icons/filter-lines.svg?react';
import ShareIcon from '@/assets/icons/share.svg?react';
import { Button, SearchBar } from '@/common/components';
import { cn } from '@/lib/utils';

import { RouteAddressesTab, RouteGroupsTab } from './components';

type Tab = 'groups' | 'addresses';
const TABS: Tab[] = ['groups', 'addresses'];

export const AdminRoutesPage = () => {
  const [activeTab, setActiveTab] = useState<Tab>('groups');
  const [search, setSearch] = useState('');

  return (
    <div className="bg-grey-200 min-h-screen px-8 py-8">
      <div className="flex flex-col gap-8">
        {/* Header */}
        <h1 className="text-grey-500">Routes</h1>

        {/* Tabs */}
        <div className="flex flex-col gap-0">
          <div className="flex gap-12">
            {TABS.map((tab) => (
              <button
                key={tab}
                type="button"
                onClick={() => setActiveTab(tab)}
                className={cn(
                  'font-nunito text-h2 pb-2 capitalize transition-colors',
                  activeTab === tab
                    ? 'text-grey-500 border-b-2 border-blue-300 font-bold'
                    : 'text-grey-400 font-normal'
                )}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>
          <hr className="border-grey-300" />
        </div>

        {/* Toolbar */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
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

        {/* Tab content */}
        {activeTab === 'groups' && <RouteGroupsTab />}
        {activeTab === 'addresses' && <RouteAddressesTab />}
      </div>
    </div>
  );
};
