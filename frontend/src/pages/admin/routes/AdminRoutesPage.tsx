import { useState } from 'react';
import { Link } from 'react-router-dom';

import FilterLinesIcon from '@/assets/icons/filter-lines.svg?react';
import ShareIcon from '@/assets/icons/share.svg?react';
import { Button, SearchBar } from '@/common/components';
import { cn } from '@/lib/utils';

import { RouteAddressesTab, RouteGroupsTab } from './components';

const TABS = [
  {
    label: 'Groups',
    render: () => <RouteGroupsTab />,
  },
  {
    label: 'Addresses',
    render: () => <RouteAddressesTab />,
  },
] as const;

export const AdminRoutesPage = () => {
  const [activeLabel, setActiveLabel] = useState<string>(TABS[0].label);

  // TODO: Add search and filter logic
  const [search, setSearch] = useState('');

  const activeTab = TABS.find((t) => t.label === activeLabel) ?? TABS[0];

  return (
    <div className="flex flex-col gap-8">
      {/* Header */}
      <h1 className="text-grey-500">Routes</h1>

      {/* Tabs */}
      <div className="flex flex-col gap-0">
        <div className="flex gap-12">
          {TABS.map((tab) => (
            <button
              key={tab.label}
              type="button"
              onClick={() => setActiveLabel(tab.label)}
              className={cn(
                'font-nunito text-h2 pb-2 capitalize transition-colors',
                activeLabel === tab.label
                  ? 'text-grey-500 border-b-2 border-blue-300 font-bold'
                  : 'text-grey-400 font-normal'
              )}
            >
              {tab.label}
            </button>
          ))}
        </div>
        <hr className="border-grey-300" />
      </div>

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

      {activeTab.render()}
    </div>
  );
};
